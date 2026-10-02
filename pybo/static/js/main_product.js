/**
 * main_product.js
 * 권역별 여행 상품 탭, 지도 버튼, 캔버스 권역 하이라이트 동기화 스크립트
 */

document.addEventListener('DOMContentLoaded', () => {
    const tabButtons = document.querySelectorAll('#pills-tab button[data-bs-toggle="pill"]');
    const mapButtons = document.querySelectorAll('#map-choice .map-btn, #map-choice .map-btn-all');
    const carouselEl = document.getElementById('carouselExampleAutoplaying');
    const mapCanvas = document.getElementById('map-canvas');
    const sourceImg = document.getElementById('map-source-img');

    // 권역별 슬라이드 인덱스 매핑
    const regionToSlide = {
        'all': 0,
        'sudo': 1,
        'gang': 2,
        'chung': 3,
        'geong': 4,
        'jeon': 5,
        'jeju': 6
    };

    // 권역별 플러드필(Flood Fill) 탐색 시드 좌표 (370 x 539 해상도 기준)
    const regionSeeds = {
        'sudo': [
            { x: 105, y: 125 }, // 서울
            { x: 130, y: 80 },  // 경기북부
            { x: 125, y: 165 }, // 경기남부
            { x: 80, y: 135 },  // 인천
            { x: 65, y: 105 }   // 강화
        ],
        'gang': [
            { x: 210, y: 80 },  // 춘천/인제
            { x: 250, y: 120 }, // 강릉
            { x: 200, y: 140 }, // 원주
            { x: 300, y: 55 }   // 울릉/독도 원형 인셋
        ],
        'chung': [
            { x: 100, y: 220 }, // 충남북부
            { x: 90, y: 250 },  // 충남남부
            { x: 165, y: 195 }, // 충북북부
            { x: 185, y: 235 }, // 충북남부
            { x: 135, y: 260 }, // 대전
            { x: 125, y: 225 }  // 세종
        ],
        'geong': [
            { x: 230, y: 200 }, // 경북북부
            { x: 265, y: 220 }, // 울진/영덕
            { x: 225, y: 265 }, // 구미/김천
            { x: 265, y: 275 }, // 포항/경주
            { x: 240, y: 310 }, // 대구
            { x: 190, y: 340 }, // 진주
            { x: 230, y: 350 }, // 창원
            { x: 295, y: 335 }, // 울산
            { x: 275, y: 375 }  // 부산
        ],
        'jeon': [
            { x: 110, y: 300 }, // 전북북부
            { x: 140, y: 320 }, // 전북남부
            { x: 95, y: 360 },  // 전남북부
            { x: 105, y: 375 }, // 광주
            { x: 80, y: 410 },  // 목포/해남
            { x: 125, y: 410 }  // 순천/여수
        ],
        'jeju': [
            { x: 85, y: 515 },
            { x: 75, y: 515 },
            { x: 95, y: 515 }
        ]
    };

    // 지도 상단에 표시할 권역별 라벨 배지 좌표
    const regionBadges = {
        'sudo': { text: '📍 수도권', x: 115, y: 135 },
        'gang': { text: '📍 강원권', x: 225, y: 105 },
        'chung': { text: '📍 충청권', x: 130, y: 235 },
        'geong': { text: '📍 경상권', x: 245, y: 295 },
        'jeon': { text: '📍 전라권', x: 110, y: 370 },
        'jeju': { text: '📍 제주권', x: 85, y: 485 }
    };

    let baseImageData = null;
    let currentActiveRegion = 'all';

    /**
     * 지도 원본 이미지(map_basic.png) 로드 및 원본 픽셀 데이터 캐싱
     */
    function initMapCanvas() {
        if (!mapCanvas || !sourceImg) return;
        const ctx = mapCanvas.getContext('2d', { willReadFrequently: true });
        if (!ctx) return;

        function loadBaseImage() {
            mapCanvas.width = 370;
            mapCanvas.height = 539;
            ctx.clearRect(0, 0, 370, 539);
            ctx.drawImage(sourceImg, 0, 0, 370, 539);
            baseImageData = ctx.getImageData(0, 0, 370, 539);
            renderMapHighlight(currentActiveRegion);
        }

        if (sourceImg.complete && sourceImg.naturalWidth > 0) {
            loadBaseImage();
        } else {
            sourceImg.onload = loadBaseImage;
        }
    }

    /**
     * 주어진 시드 좌표로부터 연결된 흰색 육지 영역을 지정 색상으로 플러드필 채우기
     */
    function floodFillRegion(data, width, height, startX, startY, fillR, fillG, fillB, fillA) {
        function getIdx(x, y) {
            return (y * width + x) * 4;
        }

        function isFillableWhite(x, y) {
            if (x < 0 || x >= width || y < 0 || y >= height) return false;
            const idx = getIdx(x, y);
            const r = data[idx];
            const g = data[idx + 1];
            const b = data[idx + 2];
            const a = data[idx + 3];
            // 투명 배경이나 회색 경계선이 아닌 순백색 내륙만 채움
            return a > 150 && r > 220 && g > 220 && b > 220;
        }

        // 반경 25px 내의 가장 가까운 흰색 픽셀 탐색
        let seedX = -1, seedY = -1;
        if (isFillableWhite(startX, startY)) {
            seedX = startX;
            seedY = startY;
        } else {
            outer: for (let r = 1; r <= 25; r++) {
                for (let dx = -r; dx <= r; dx++) {
                    for (let dy = -r; dy <= r; dy++) {
                        if (Math.abs(dx) === r || Math.abs(dy) === r) {
                            const nx = startX + dx;
                            const ny = startY + dy;
                            if (isFillableWhite(nx, ny)) {
                                seedX = nx;
                                seedY = ny;
                                break outer;
                            }
                        }
                    }
                }
            }
        }

        if (seedX === -1) return;

        const queue = [seedX, seedY];
        const visited = new Uint8Array(width * height);
        visited[seedY * width + seedX] = 1;

        while (queue.length > 0) {
            const cy = queue.pop();
            const cx = queue.pop();
            const idx = getIdx(cx, cy);

            data[idx] = fillR;
            data[idx + 1] = fillG;
            data[idx + 2] = fillB;
            data[idx + 3] = fillA;

            const neighbors = [
                cx + 1, cy,
                cx - 1, cy,
                cx, cy + 1,
                cx, cy - 1
            ];

            for (let i = 0; i < neighbors.length; i += 2) {
                const nx = neighbors[i];
                const ny = neighbors[i + 1];
                if (nx >= 0 && nx < width && ny >= 0 && ny < height) {
                    const pos = ny * width + nx;
                    if (!visited[pos] && isFillableWhite(nx, ny)) {
                        visited[pos] = 1;
                        queue.push(nx, ny);
                    }
                }
            }
        }
    }

    /**
     * 권역 뱃지(Pill Label) 그리기
     */
    function drawRegionBadge(ctx, badge) {
        ctx.save();
        const text = badge.text;
        ctx.font = 'bold 13px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans KR", sans-serif';
        const textWidth = ctx.measureText(text).width;
        const padX = 10, padY = 6;
        const w = textWidth + padX * 2;
        const h = 26;
        const x = Math.max(10, Math.min(370 - w - 10, badge.x - w / 2));
        const y = Math.max(10, Math.min(539 - h - 10, badge.y - h / 2));

        // 그림자 효과
        ctx.shadowColor = 'rgba(0, 0, 0, 0.3)';
        ctx.shadowBlur = 8;
        ctx.shadowOffsetY = 2;

        // 코랄 배경 알약 뱃지
        ctx.fillStyle = '#E76F5F';
        ctx.beginPath();
        if (typeof ctx.roundRect === 'function') {
            ctx.roundRect(x, y, w, h, 13);
        } else {
            ctx.rect(x, y, w, h);
        }
        ctx.fill();

        // 텍스트 출력
        ctx.shadowColor = 'transparent';
        ctx.fillStyle = '#ffffff';
        ctx.textBaseline = 'middle';
        ctx.textAlign = 'center';
        ctx.fillText(text, x + w / 2, y + h / 2);
        ctx.restore();
    }

    /**
     * 활성화된 권역 지도에 색상 하이라이트 렌더링
     */
    function renderMapHighlight(activeRegion) {
        if (!mapCanvas || !baseImageData) return;
        const ctx = mapCanvas.getContext('2d');
        if (!ctx) return;

        // 전체 또는 미선택 시 기본 지도 원본 출력
        if (!activeRegion || activeRegion === 'all' || !regionSeeds[activeRegion]) {
            ctx.putImageData(baseImageData, 0, 0);
            return;
        }

        // 원본 복사본 생성 후 해당 권역 시드들에 대해 색 채우기 (#1D3557 네이비 색상)
        const currentData = new ImageData(new Uint8ClampedArray(baseImageData.data), 370, 539);
        const seeds = regionSeeds[activeRegion] || [];
        seeds.forEach(pt => {
            floodFillRegion(currentData.data, 370, 539, pt.x, pt.y, 29, 53, 87, 240);
        });

        // 캔버스에 색 채워진 지도 반영
        ctx.putImageData(currentData, 0, 0);

        // 상단에 눈에 띄는 권역 라벨 뱃지 표시
        if (regionBadges[activeRegion]) {
            drawRegionBadge(ctx, regionBadges[activeRegion]);
        }
    }

    /**
     * 클릭 좌표로부터 해당하는 권역 키 식별
     */
    function getRegionFromCoord(x, y) {
        if (x < 0 || x >= 370 || y < 0 || y >= 539) return null;
        if (!baseImageData) return null;

        // 클릭 지점 근처에 육지가 존재하는지 확인
        const idx = (y * 370 + x) * 4;
        if (baseImageData.data[idx + 3] < 30) {
            let hasLand = false;
            for (let r = 1; r <= 8; r += 2) {
                for (let dx = -r; dx <= r; dx += 2) {
                    for (let dy = -r; dy <= r; dy += 2) {
                        const nx = x + dx, ny = y + dy;
                        if (nx >= 0 && nx < 370 && ny >= 0 && ny < 539) {
                            if (baseImageData.data[(ny * 370 + nx) * 4 + 3] > 100) {
                                hasLand = true;
                                break;
                            }
                        }
                    }
                    if (hasLand) break;
                }
                if (hasLand) break;
            }
            if (!hasLand) return null;
        }

        // 권역별 지리적 경계 판별
        if (y >= 475) return 'jeju';
        if (y < 170 && x >= 165) return 'gang';
        if (y < 185 && x < 165) return 'sudo';
        if (y >= 185 && y < 285 && x < 165) return 'chung';
        if (y >= 170 && x >= 165) return 'geong';
        if (y >= 285 && x < 180) return 'jeon';
        return null;
    }

    /**
     * 특정 권역만 화면에 표시하도록 전환하는 핵심 함수
     * @param {string} region ('all', 'sudo', 'gang', 'chung', 'geong', 'jeon', 'jeju')
     */
    function activateRegion(region) {
        if (!region) region = 'all';
        currentActiveRegion = region;

        // 1. 오른쪽 상품 영역: 해당 권역 패널만 보이도록 처리하고 다른 모든 패널 숨김
        const targetPaneId = `pills-${region}`;
        const allPanes = document.querySelectorAll('.tab-content .tab-pane');
        allPanes.forEach(pane => {
            if (pane.id === targetPaneId) {
                pane.classList.add('show', 'active');
            } else {
                pane.classList.remove('show', 'active');
            }
        });

        // 2. 상단 탭 버튼 active 클래스 동기화
        tabButtons.forEach(btn => {
            const btnRegion = btn.dataset.region || 'all';
            if (btnRegion === region) {
                btn.classList.add('active');
                btn.setAttribute('aria-selected', 'true');
            } else {
                btn.classList.remove('active');
                btn.setAttribute('aria-selected', 'false');
            }
        });

        // 3. 좌측 지도 버튼 active 상태 동기화
        const currentMapBtns = document.querySelectorAll('#map-choice .map-btn, #map-choice .map-btn-all');
        currentMapBtns.forEach(btn => {
            const btnRegion = btn.dataset.region || 'all';
            if (btnRegion === region) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });

        // 4. 상단 캐러셀 슬라이드 이동
        if (carouselEl && window.bootstrap && typeof window.bootstrap.Carousel !== 'undefined') {
            const slideIndex = regionToSlide[region];
            if (slideIndex !== undefined) {
                const carouselInstance = bootstrap.Carousel.getOrCreateInstance(carouselEl);
                if (carouselInstance) {
                    carouselInstance.to(slideIndex);
                }
            }
        }

        // 5. 지도 캔버스 권역 색상 하이라이트 렌더링
        renderMapHighlight(region);
    }

    /**
     * 지도 캔버스 클릭 시 해당 권역 선택 이벤트 연동
     */
    if (mapCanvas) {
        mapCanvas.addEventListener('click', (event) => {
            const rect = mapCanvas.getBoundingClientRect();
            const scaleX = mapCanvas.width / rect.width;
            const scaleY = mapCanvas.height / rect.height;
            const clickX = Math.round((event.clientX - rect.left) * scaleX);
            const clickY = Math.round((event.clientY - rect.top) * scaleY);

            const clickedRegion = getRegionFromCoord(clickX, clickY);
            if (!clickedRegion) return;

            // 이미 활성화된 권역을 다시 클릭하면 전체로 복귀
            if (currentActiveRegion === clickedRegion) {
                activateRegion('all');
            } else {
                activateRegion(clickedRegion);
            }
        });

        mapCanvas.addEventListener('mousemove', (event) => {
            const rect = mapCanvas.getBoundingClientRect();
            const scaleX = mapCanvas.width / rect.width;
            const scaleY = mapCanvas.height / rect.height;
            const moveX = Math.round((event.clientX - rect.left) * scaleX);
            const moveY = Math.round((event.clientY - rect.top) * scaleY);

            const hoveredRegion = getRegionFromCoord(moveX, moveY);
            mapCanvas.style.cursor = hoveredRegion ? 'pointer' : 'default';
        });
    }

    // 상단 탭 버튼 클릭 이벤트 리스너 등록
    tabButtons.forEach(tabBtn => {
        tabBtn.addEventListener('click', (e) => {
            e.preventDefault();
            const region = tabBtn.dataset.region || 'all';
            activateRegion(region);
        });
    });

    // 좌측 지도 권역 버튼 및 전체 버튼 클릭 이벤트 리스너 등록
    mapButtons.forEach(mapBtn => {
        mapBtn.addEventListener('click', (e) => {
            e.preventDefault();
            const region = mapBtn.dataset.region || 'all';

            // 이미 활성화된 권역 버튼을 다시 클릭하면 '전체' 보기로 복귀
            if (region !== 'all' && currentActiveRegion === region) {
                activateRegion('all');
            } else {
                activateRegion(region);
            }
        });
    });

    // 초기 캔버스 초기화 및 활성화된 탭 상태 동기화
    initMapCanvas();
    const activeTab = document.querySelector('#pills-tab button.nav-link.active') ||
                      document.querySelector('#map-choice .map-btn.active');
    const initialRegion = activeTab ? (activeTab.dataset.region || 'all') : 'all';
    activateRegion(initialRegion);
});
