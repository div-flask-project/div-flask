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

    // 권역별 플러드필(Flood Fill) 정밀 시드 좌표 (370 x 539 해상도 기준, 타 권역 침범 없는 내륙 검증 좌표)
    const regionSeeds = {
        'sudo': [
            { x: 95, y: 117 },  // 서울
            { x: 113, y: 121 }, // 경기
            { x: 71, y: 126 }   // 인천/강화
        ],
        'gang': [
            { x: 209, y: 98 },  // 강원 본토
            { x: 301, y: 47 }   // 울릉/독도 원형 인셋
        ],
        'chung': [
            { x: 86, y: 235 },  // 충남
            { x: 169, y: 209 }, // 충북
            { x: 114, y: 225 }, // 세종
            { x: 131, y: 253 }  // 대전
        ],
        'geong': [
            { x: 251, y: 251 }, // 경북
            { x: 236, y: 310 }, // 대구
            { x: 207, y: 359 }, // 경남
            { x: 298, y: 340 }, // 울산
            { x: 283, y: 378 }, // 부산
            { x: 352, y: 261 }  // 울릉도 실도
        ],
        'jeon': [
            { x: 109, y: 323 }, // 전북
            { x: 90, y: 406 },  // 전남
            { x: 79, y: 385 },  // 광주
            { x: 36, y: 472 }   // 진도/도서
        ],
        'jeju': [
            { x: 84, y: 518 }   // 제주 본섬
        ]
    };

    const regionCodes = {
        'sudo': 1,
        'gang': 2,
        'chung': 3,
        'geong': 4,
        'jeon': 5,
        'jeju': 6
    };

    const codeToRegion = {
        1: 'sudo',
        2: 'gang',
        3: 'chung',
        4: 'geong',
        5: 'jeon',
        6: 'jeju'
    };

    // 지도 상단에 표시할 권역별 라벨 배지 좌표 (각 권역 중앙 앵커)
    const regionBadges = {
        'sudo': { text: '📍 수도권', x: 111, y: 121 },
        'gang': { text: '📍 강원권', x: 209, y: 98 },
        'chung': { text: '📍 충청권', x: 128, y: 223 },
        'geong': { text: '📍 경상권', x: 239, y: 292 },
        'jeon': { text: '📍 전라권', x: 97, y: 369 },
        'jeju': { text: '📍 제주권', x: 84, y: 490 }
    };

    let baseImageData = null;
    let regionGrid = null; // Uint8Array(370 * 539) 픽셀별 권역 코드 매핑 (1~6)
    let currentActiveRegion = 'all';

    /**
     * 흰색 내륙 픽셀 여부 판별 (배경 투명 및 경계선 제외)
     */
    function isFillableWhite(data, x, y, width, height) {
        if (x < 0 || x >= width || y < 0 || y >= height) return false;
        const idx = (y * width + x) * 4;
        const r = data[idx];
        const g = data[idx + 1];
        const b = data[idx + 2];
        const a = data[idx + 3];
        return a > 150 && r > 220 && g > 220 && b > 220;
    }

    /**
     * 지도 원본 이미지(map_basic.png) 로드 및 권역별 픽셀 그리드(regionGrid) 사전 계산
     */
    function buildRegionGrid(data, width, height) {
        const grid = new Uint8Array(width * height);

        for (const [region, seeds] of Object.entries(regionSeeds)) {
            const code = regionCodes[region];
            if (!code) continue;

            for (const pt of seeds) {
                let sx = pt.x;
                let sy = pt.y;
                if (!isFillableWhite(data, sx, sy, width, height)) {
                    // 미세 오차 대비 최대 2px 내에서만 흰색 픽셀 탐색 (경계선 침범 방지)
                    let found = false;
                    for (let r = 1; r <= 2; r++) {
                        for (let dx = -r; dx <= r; dx++) {
                            for (let dy = -r; dy <= r; dy++) {
                                if (isFillableWhite(data, sx + dx, sy + dy, width, height)) {
                                    sx = sx + dx;
                                    sy = sy + dy;
                                    found = true;
                                    break;
                                }
                            }
                            if (found) break;
                        }
                        if (found) break;
                    }
                    if (!found) continue;
                }

                const seedPos = sy * width + sx;
                if (grid[seedPos] !== 0) continue;

                const queue = [sx, sy];
                grid[seedPos] = code;

                while (queue.length > 0) {
                    const cy = queue.pop();
                    const cx = queue.pop();

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
                            if (grid[pos] === 0 && isFillableWhite(data, nx, ny, width, height)) {
                                grid[pos] = code;
                                queue.push(nx, ny);
                            }
                        }
                    }
                }
            }
        }
        return grid;
    }

    /**
     * 지도 원본 이미지(map_basic.png) 로드 및 원본 픽셀 데이터, 권역 그리드 캐싱
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
            regionGrid = buildRegionGrid(baseImageData.data, 370, 539);
            renderMapHighlight(currentActiveRegion);
        }

        if (sourceImg.complete && sourceImg.naturalWidth > 0) {
            loadBaseImage();
        } else {
            sourceImg.onload = loadBaseImage;
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
        if (!activeRegion || activeRegion === 'all' || !regionCodes[activeRegion] || !regionGrid) {
            ctx.putImageData(baseImageData, 0, 0);
            return;
        }

        const targetCode = regionCodes[activeRegion];
        const currentData = new ImageData(new Uint8ClampedArray(baseImageData.data), 370, 539);
        const d = currentData.data;
        const totalPixels = 370 * 539;

        // 해당 권역으로 확정된 픽셀만 하이라이트 색상(#1D3557 네이비) 적용
        for (let i = 0; i < totalPixels; i++) {
            if (regionGrid[i] === targetCode) {
                const idx = i * 4;
                d[idx] = 29;     // R
                d[idx + 1] = 53; // G
                d[idx + 2] = 87; // B
                d[idx + 3] = 240;// A
            }
        }

        // 캔버스에 색 채워진 지도 반영
        ctx.putImageData(currentData, 0, 0);

        // 상단에 눈에 띄는 권역 라벨 뱃지 표시
        if (regionBadges[activeRegion]) {
            drawRegionBadge(ctx, regionBadges[activeRegion]);
        }
    }

    /**
     * 클릭/호버 좌표로부터 해당하는 권역 키 식별 (정밀 픽셀 및 반경 3px 근접 스냅)
     */
    function getRegionFromCoord(x, y) {
        if (x < 0 || x >= 370 || y < 0 || y >= 539) return null;
        if (!regionGrid) return null;

        const pos = y * 370 + x;
        const code = regionGrid[pos];
        if (code > 0 && codeToRegion[code]) {
            return codeToRegion[code];
        }

        // 경계선(1~2px 회색선)이나 해안가 클릭 시 반경 3px 내 인접 권역 탐색
        for (let r = 1; r <= 3; r++) {
            for (let dx = -r; dx <= r; dx++) {
                for (let dy = -r; dy <= r; dy++) {
                    const nx = x + dx;
                    const ny = y + dy;
                    if (nx >= 0 && nx < 370 && ny >= 0 && ny < 539) {
                        const nearCode = regionGrid[ny * 370 + nx];
                        if (nearCode > 0 && codeToRegion[nearCode]) {
                            return codeToRegion[nearCode];
                        }
                    }
                }
            }
        }

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

