// Cursor Tracking
document.addEventListener('mousemove', (e) => {
    const glow = document.getElementById('cursor-glow');
    if (!glow) return;
    glow.style.left = e.clientX + 'px';
    glow.style.top = e.clientY + 'px';
});

// Cloud Status Check Function
function checkCloudStatus() {
    // Stub implementation: Log cloud status or perform minimal check
    console.log('Checking cloud status...');
    // TODO: Implement actual cloud availability check if needed
}

// Global variables
let currentReportData = null;
let allTickers = [];
let isDropdownInitialized = false;
let currentFocus = -1; // For keyboard navigation

// Global function to select a ticker from dropdown
function selectTicker(ticker) {
    const input = document.getElementById('ticker-input');
    if (input) {
        input.value = ticker;
        const dropdown = document.getElementById('ticker-dropdown');
        if (dropdown) {
            dropdown.classList.remove('visible');
            dropdown.classList.add('hidden');
        }
        input.focus();
    }
}

// Load Tickers
async function initializeTickerDropdown() {
    if (isDropdownInitialized) return;
    
    const input = document.getElementById('ticker-input');
    const dropdown = document.getElementById('ticker-dropdown');
    
    if (!input || !dropdown) {
        console.error('Ticker input or dropdown element not found');
        return;
    }
    
    // Show loading state
    const originalPlaceholder = input.placeholder;
    input.placeholder = 'Loading tickers...';

    let controller;
    let timeoutId;
    
    try {
        // Create a new AbortController for this request
        controller = new AbortController();
        
        // Set a 5 second timeout for the request
        const timeoutPromise = new Promise((_, reject) => {
            timeoutId = setTimeout(() => {
                const error = new Error('Ticker fetch timed out after 5 seconds');
                error.name = 'TimeoutError';
                controller.abort();
                reject(error);
            }, 5000);
        });
        
        // Race the fetch against the timeout
        const response = await Promise.race([
            fetch('/api/tickers', { 
                signal: controller.signal,
                cache: 'no-store'  // Prevent caching to get fresh data
            }),
            timeoutPromise
        ]);
        
        // Clear the timeout since the request completed in time
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            const errorText = await response.text().catch(() => 'No details');
            throw new Error(`HTTP error! status: ${response.status}, details: ${errorText}`);
        }
        
        const data = await response.json();
        
        // Ensure we have an array of tickers
        if (data && Array.isArray(data.tickers) && data.tickers.length > 0) {
            allTickers = data.tickers;
            console.log("✓ Loaded", allTickers.length, "tickers from server");
        } else {
            throw new Error('No tickers returned from server');
        }
        
    } catch (e) {
        console.warn("Failed to load tickers from server, using fallback:", e);
        // Fallback to a default set of tickers if API fails
        allTickers = ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'HINDUNILVR.NS'];
    } finally {
        // Initialize dropdown with whatever tickers we have
        if (input && dropdown) {
            setupTickerDropdown(input, dropdown);
            isDropdownInitialized = true;
            input.placeholder = originalPlaceholder;
        }
    }
}

function setupTickerDropdown(input, dropdown) {
    // Function to filter tickers based on input
    function filterTickers(input) {
        const searchTerm = input.trim().toLowerCase();
        let filteredTickers = [];
        
        if (searchTerm.length > 0) {
            filteredTickers = allTickers.filter(ticker => 
                ticker.toLowerCase().includes(searchTerm)
            );
        } else {
            filteredTickers = [...allTickers];
        }
        
        renderDropdown(filteredTickers);
        
        if (filteredTickers.length > 0) {
            toggleDropdown(true);
        } else {
            dropdown.innerHTML = '<li style="padding: 12px 20px; color: #ff6b6b; text-align: center;">No matching tickers found</li>';
        }
        
        // Reset keyboard navigation
        currentFocus = -1;
    }

    // Function to render ticker dropdown
    function renderDropdown(tickers) {
        if (!tickers || tickers.length === 0) {
            dropdown.innerHTML = '<li style="padding: 12px 20px; color: #999; text-align: center;">No tickers available</li>';
            return;
        }
        
        dropdown.innerHTML = tickers.map(ticker => {
            const displayName = ticker.split('.').length > 1 ? ticker.split('.')[0] : ticker;
            return `
                <li 
                    onclick="selectTicker('${ticker}')"
                    onmouseover="this.classList.add('highlighted')"
                    onmouseout="this.classList.remove('highlighted')"
                    style="padding: 12px 20px; cursor: pointer; position: relative; transition: all 0.2s ease;"
                >
                    <span class="ticker-symbol" style="font-weight: 600; color: #4fc3f7; margin-right: 8px;">${ticker}</span>
                    <span class="ticker-name" style="opacity: 0.8; font-size: 0.9em;">${displayName}</span>
                </li>
            `;
        }).join('');
    }

    // Toggle dropdown visibility
    function toggleDropdown(show) {
        if (show) {
            dropdown.classList.remove('hidden');
            dropdown.classList.add('visible');
        } else {
            dropdown.classList.remove('visible');
            dropdown.classList.add('hidden');
        }
    }

    // Set active item for keyboard navigation
    function setActive(items) {
        if (!items) return;
        
        // Remove active class from all items
        for (let i = 0; i < items.length; i++) {
            items[i].classList.remove('highlighted');
        }
        
        // Add active class to current item
        if (currentFocus >= 0 && currentFocus < items.length) {
            items[currentFocus].classList.add('highlighted');
            items[currentFocus].scrollIntoView({ block: 'nearest' });
            
            // Update input value
            const ticker = items[currentFocus].querySelector('.ticker-symbol')?.textContent;
            if (ticker) {
                input.value = ticker;
            }
        }
    }

    // Input events for search filtering
    input.addEventListener('input', () => {
        filterTickers(input.value);
    });
    
    // Focus/blur handling for dropdown
    input.addEventListener('focus', () => {
        if (allTickers.length > 0) {
            filterTickers(input.value);
            toggleDropdown(true);
        }
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!input.contains(e.target) && !dropdown.contains(e.target)) {
            toggleDropdown(false);
        }
    });
    
    // Keyboard navigation
    input.addEventListener('keydown', (e) => {
        const items = dropdown.getElementsByTagName('li');
        
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            currentFocus = Math.min(currentFocus + 1, items.length - 1);
            setActive(items);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            currentFocus = Math.max(currentFocus - 1, -1);
            setActive(items);
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (currentFocus > -1 && items[currentFocus]) {
                items[currentFocus].click();
            } else {
                // Trigger analysis if the ticker is selected from dropdown
                setTimeout(() => runAnalysis(), 100);
            }
        } else if (e.key === 'Escape') {
            toggleDropdown(false);
        }
    });
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    initializeTickerDropdown();
    startNewsTicker('NSEI');
    loadInitialNews();
    
    // Initialize cloud status checking
    const useCloudToggle = document.getElementById('use_cloud');
    if (useCloudToggle) {
        checkCloudStatus();
        useCloudToggle.addEventListener('change', checkCloudStatus);
    }
});

// UI Helpers
function updateLabel(input) {
    document.getElementById('val_' + input.id).innerText = input.value;
}

// Trading Mode Logic
let currentMode = 'Swing';

function setMode(mode) {
    currentMode = mode;
    
    // Update Buttons
    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.innerText.includes(mode) || (mode === 'Intraday' && btn.innerText.includes('Day')) || (mode === 'LongTerm' && btn.innerText.includes('Long'))) {
            btn.classList.add('active');
        }
    });

    // Adjust UI/Defaults based on Mode
    const strategyPeriod = document.getElementById('strategy_period');
    const futureDays = document.getElementById('future_days');
    const timeSteps = document.getElementById('time_steps');

    if (mode === 'Scalping') {
        strategyPeriod.value = '1mo';
        strategyPeriod.disabled = true; // Force short period for 1m data
        futureDays.value = 5;
        timeSteps.value = 30;
    } else if (mode === 'Intraday') {
        strategyPeriod.value = '3mo';
        strategyPeriod.disabled = true;
        futureDays.value = 15;
        timeSteps.value = 60;
    } else if (mode === 'Swing') {
        strategyPeriod.value = '2y';
        strategyPeriod.disabled = false;
        futureDays.value = 21;
        timeSteps.value = 60;
    } else if (mode === 'LongTerm') {
        strategyPeriod.value = '5y';
        strategyPeriod.disabled = false;
        futureDays.value = 60;
        timeSteps.value = 90;
    }
    
    // Update labels
    updateLabel(futureDays);
    updateLabel(timeSteps);
}

async function autoTune() {
    const tickerInput = document.getElementById('ticker-input');
    if (!tickerInput) {
        console.error('Ticker input element not found');
        return;
    }
    
    const ticker = tickerInput.value.trim();
    if (!ticker) {
        alert("Please enter a ticker first.");
        return;
    }
    
    // Find the button that triggered the event
    const btn = document.querySelector('button[onclick="autoTune()"]');
    if (!btn) {
        console.error('Auto-tune button not found');
        return;
    }
    
    const originalText = btn.innerText;
    btn.innerText = "⏳ Tuning...";
    btn.disabled = true;

    try {
        const response = await fetch('/auto-tune', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({ ticker: ticker, trading_mode: currentMode })
        });
        
        // First check if the response is JSON
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const errorText = await response.text();
            throw new Error(`Expected JSON but got ${contentType}. Response: ${errorText.substring(0, 200)}...`);
        }
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            const errorMessage = errorData.detail || errorData.message || 'Unknown error';
            throw new Error(`Auto-tune failed (${response.status}): ${errorMessage}`);
        }
        
        const params = await response.json();
        
        // Map params to inputs
        const fields = [
            'strategy_period', 'future_days', 'epochs', 'batch_size', 
            'time_steps', 'train_split', 'lstm_units_1', 'lstm_units_2',
            'dense_units', 'dropout_rate'
        ];

        fields.forEach(id => {
            if (params[id] !== undefined && document.getElementById(id)) {
                const el = document.getElementById(id);
                el.value = params[id];
                if (document.getElementById('val_' + id)) {
                    document.getElementById('val_' + id).innerText = params[id];
                }
                // Visual feedback: Flash green to show update
                el.style.transition = "background-color 0.5s";
                el.style.backgroundColor = "rgba(0, 255, 157, 0.3)";
                setTimeout(() => el.style.backgroundColor = "", 1000);
            }
        });
        
        document.getElementById('fast_mode').checked = false; // Disable fast mode to use new params
        alert(`✅ AI has optimized hyperparameters for ${ticker}. Fast Mode disabled.`);
    } catch (e) {
        alert("Error: " + e.message);
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
    }
}

async function runAnalysis() {
    const tickerInput = document.getElementById('ticker-input');
    if (!tickerInput) {
        console.error('Ticker input element not found');
        return;
    }
    
    const ticker = tickerInput.value.trim();
    if (!ticker) {
        alert("Please enter a ticker first.");
        return;
    }
    
    const dashboard = document.getElementById('dashboard');
    if (!dashboard) {
        console.error('Dashboard element not found');
        return;
    }
    
    const loading = document.getElementById('loading');
    if (!loading) {
        console.error('Loading element not found');
        return;
    }
    
    // Auto-save previous report to history
    if (currentReportData) {
        saveCurrentReport(true);
    }
    
    // Reset UI
    // dashboard.classList.add('hidden'); // Keep old report visible
    loading.classList.remove('hidden');
    
    // Generate Request ID
    const requestId = 'req-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
    
    // Start Polling Progress
    const progressInterval = setInterval(async () => {
        try {
            const res = await fetch(`/progress/${requestId}`);
            if (!res.ok) {
                console.error('Progress fetch failed:', res.status);
                clearInterval(progressInterval);
                return;
            }
            
            try {
                const pData = await res.json();
                if (pData && pData.progress !== undefined) {
                    const pct = pData.progress;
                    const loadingText = document.getElementById('loading-text');
                    const progressBar = document.getElementById('progress-bar');
                    if (loadingText) loadingText.innerText = `Training Model: ${pct}%`;
                    if (progressBar) progressBar.style.width = `${pct}%`;
                }
            } catch (e) {
                console.error('Error parsing progress:', e);
                clearInterval(progressInterval);
            }
        } catch (e) {
            console.error('Progress fetch error:', e);
            clearInterval(progressInterval);
        }
    }, 1000);

    // Collect Hyperparameters with null checks and defaults
    const getElementValue = (id, defaultValue) => {
        const el = document.getElementById(id);
        return el ? el.value : defaultValue;
    };

    const getElementChecked = (id, defaultValue) => {
        const el = document.getElementById(id);
        return el ? el.checked : defaultValue;
    };

    const params = {
        ticker: ticker,
        strategy_period: getElementValue('strategy_period', '1y'),
        future_days: parseInt(getElementValue('future_days', '10')),
        epochs: parseInt(getElementValue('epochs', '50')),
        batch_size: parseInt(getElementValue('batch_size', '32')),
        time_steps: parseInt(getElementValue('time_steps', '60')),
        train_split: parseInt(getElementValue('train_split', '80')),
        lstm_units_1: parseInt(getElementValue('lstm_units_1', '50')),
        lstm_units_2: parseInt(getElementValue('lstm_units_2', '50')),
        dense_units: parseInt(getElementValue('dense_units', '25')),
        dropout_rate: parseFloat(getElementValue('dropout_rate', '0.2')),
        fast_mode: getElementChecked('fast_mode', false),
        use_cloud: getElementChecked('use_cloud', false),
        request_id: requestId,
        trading_mode: currentMode
    };

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params)
        });

        if (!response.ok) throw new Error('Analysis failed');
        
        const data = await response.json();
        currentReportData = data; // Store for saving
        renderDashboard(data);
        
        // Update news ticker with the analyzed ticker
        startNewsTicker(data.ticker);

        // Show news modal with ticker-specific news
        showNewsModal(data);
    } catch (error) {
        alert(error.message);
    } finally {
        clearInterval(progressInterval);
        loading.classList.add('hidden');
        dashboard.classList.remove('hidden');
    }
}

function renderDashboard(data) {
    document.getElementById('dash-title').innerText = `Analysis: ${data.ticker}`;
    
    // 2. Dataset Preview
    const dsTable = document.getElementById('dataset-table');
    if (data.dataset_preview && data.dataset_preview.length > 0) {
        const headers = Object.keys(data.dataset_preview[0]);
        dsTable.innerHTML = `
            <thead><tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr></thead>
            <tbody>${data.dataset_preview.map(row => `<tr>${headers.map(h => `<td>${row[h]}</td>`).join('')}</tr>`).join('')}</tbody>
        `;
    } else {
        dsTable.innerHTML = '<tr><td style="padding:10px; text-align:center; color:var(--text-secondary);">No dataset preview available.</td></tr>';
    }

    // 6. Future Forecast Table
    const fcTable = document.getElementById('forecast-table');
    if (data.future_dates && data.future_preds && data.future_dates.length > 0) {
        fcTable.innerHTML = `
            <thead><tr><th>Date</th><th>Predicted Close</th></tr></thead>
            <tbody>${data.future_dates.map((d, i) => `
                <tr>
                    <td>${d}</td>
                    <td>${(data.future_preds[i] || 0).toFixed(2)}</td>
                </tr>
            `).join('')}</tbody>
        `;
    } else {
        fcTable.innerHTML = '<tr><td style="padding:10px; text-align:center; color:var(--text-secondary);">No forecast data available.</td></tr>';
    }

    // 1. Metrics
    document.getElementById('final-conf').innerText = ((data.final_confidence || 0) * 100).toFixed(1) + '%';
    document.getElementById('final-label').innerText = data.final_conf_label || 'N/A';
    document.getElementById('final-label').style.color = data.final_conf_label === 'Buy' ? '#28cd41' : '#ff3b30';
    
    const lastPred = (data.future_preds && data.future_preds.length > 0) ? data.future_preds[0] : 0;
    document.getElementById('forecast-price').innerText = lastPred.toFixed(2);
    
    document.getElementById('sentiment-score').innerText = (data.sentiment_score || 0).toFixed(2);

    // Populate News List with Indian and Global sections
    const newsList = document.getElementById('news-list');
    if (data.news_items && data.news_items.indian && data.news_items.global) {
        const indianNews = data.news_items.indian.slice(0, 5);
        const globalNews = data.news_items.global.slice(0, 5);

        let html = '';

        if (indianNews.length > 0) {
            html += '<h4 style="color: #007aff; margin-bottom: 10px;">🇮🇳 Indian Market News</h4>';
            html += indianNews.map((item, index) => {
                let badgeClass = 'sent-neu';
                let badgeText = 'NEU';
                let emoji = '📰';
                if (item.sentiment > 0.05) { badgeClass = 'sent-pos'; badgeText = 'POS'; emoji = '📈'; }
                else if (item.sentiment < -0.05) { badgeClass = 'sent-neg'; badgeText = 'NEG'; emoji = '📉'; }
                // Placeholder image - in real app, fetch from news API
                const imageUrl = `https://via.placeholder.com/80x60/007aff/ffffff?text=${emoji}`;
                return `<li class="news-item" style="--item-index: ${index};">
                    <img src="${imageUrl}" alt="News Image" loading="lazy">
                    <div style="flex: 1;">
                        <span class="sentiment-badge ${badgeClass}">${emoji} ${badgeText}</span>
                        <a href="${item.link}" target="_blank" style="display: block; margin-top: 8px; color: inherit; text-decoration: none;">${item.title}</a>
                    </div>
                </li>`;
            }).join('');
        }

        if (globalNews.length > 0) {
            html += '<h4 style="color: #af52de; margin-top: 20px; margin-bottom: 10px;">🌍 Global Finance News</h4>';
            html += globalNews.map((item, index) => {
                let badgeClass = 'sent-neu';
                let badgeText = 'NEU';
                let emoji = '📰';
                if (item.sentiment > 0.05) { badgeClass = 'sent-pos'; badgeText = 'POS'; emoji = '📈'; }
                else if (item.sentiment < -0.05) { badgeClass = 'sent-neg'; badgeText = 'NEG'; emoji = '📉'; }
                // Placeholder image - in real app, fetch from news API
                const imageUrl = `https://via.placeholder.com/80x60/af52de/ffffff?text=${emoji}`;
                return `<li class="news-item" style="--item-index: ${index + indianNews.length};">
                    <img src="${imageUrl}" alt="News Image" loading="lazy">
                    <div style="flex: 1;">
                        <span class="sentiment-badge ${badgeClass}">${emoji} ${badgeText}</span>
                        <a href="${item.link}" target="_blank" style="display: block; margin-top: 8px; color: inherit; text-decoration: none;">${item.title}</a>
                    </div>
                </li>`;
            }).join('');
        }

        newsList.innerHTML = html;
    } else {
        newsList.innerHTML = '<li class="news-item" style="color:#888;">No recent news found.</li>';
    }

    // Calculate date ranges for Train/Test alignment
    const timeSteps = data.time_steps || 60;
    const trainLen = (data.train_preds || []).length;
    const dates = data.dates || [];
    
    // Align predictions with dates
    const trainDates = dates.slice(timeSteps, timeSteps + trainLen);
    const testDates = dates.slice(timeSteps + trainLen);

    // 2. Main Chart (Plotly Subplots)
    const traceActual = {
        x: dates, y: data.actual_prices || [], type: 'scatter', mode: 'lines', name: 'Actual',
        line: { color: '#1d1d1f', width: 1.5 }, xaxis: 'x', yaxis: 'y'
    };

    const traceSMA = {
        x: dates, y: data.sma20 || [], type: 'scatter', mode: 'lines', name: 'SMA20',
        line: { color: 'orange', dash: 'dot', width: 1 }, xaxis: 'x', yaxis: 'y'
    };

    const traceTrain = {
        x: trainDates, y: data.train_preds || [], type: 'scatter', mode: 'lines', name: 'Train Preds',
        line: { color: 'yellow', width: 1.5 }, xaxis: 'x', yaxis: 'y'
    };

    const traceTest = {
        x: testDates, y: data.test_preds || [], type: 'scatter', mode: 'lines', name: 'Test Preds',
        line: { color: 'cyan', width: 1.5 }, xaxis: 'x', yaxis: 'y'
    };
    
    const traceFuture = {
        x: data.future_dates || [], y: data.future_preds || [], type: 'scatter', mode: 'lines+markers', name: 'Future Forecast',
        line: { color: 'lime', width: 2 }, marker: { size: 4 }, xaxis: 'x', yaxis: 'y'
    };

    const traceBBUp = {
        x: dates, y: data.upper_bb || [], type: 'scatter', mode: 'lines', name: 'Upper BB',
        line: { color: 'rgba(0,0,0,0.1)', width: 1 }, showlegend: false, hoverinfo: 'skip', xaxis: 'x', yaxis: 'y'
    };
    const traceBBLow = {
        x: dates, y: data.lower_bb || [], type: 'scatter', mode: 'lines', name: 'Lower BB',
        line: { color: 'rgba(0,0,0,0.1)', width: 1 }, fill: 'tonexty', fillcolor: 'rgba(0,113,227,0.05)', showlegend: false, hoverinfo: 'skip', xaxis: 'x', yaxis: 'y'
    };

    const traceRSI = {
        x: dates, y: data.rsi || [], type: 'scatter', mode: 'lines', name: 'RSI',
        line: { color: '#bf5af2', width: 1.5 }, xaxis: 'x', yaxis: 'y2'
    };

    const traceMACD = {
        x: dates, y: data.macd || [], type: 'scatter', mode: 'lines', name: 'MACD',
        line: { color: '#007aff', width: 1.5 }, xaxis: 'x', yaxis: 'y3'
    };
    const traceSignal = {
        x: dates, y: data.macd_signal || [], type: 'scatter', mode: 'lines', name: 'Signal',
        line: { color: '#ff9500', width: 1.5 }, xaxis: 'x', yaxis: 'y3'
    };
    const traceHist = {
        x: dates, y: data.macd_hist || [], type: 'bar', name: 'Hist',
        marker: { color: 'rgba(255,255,255,0.3)' }, xaxis: 'x', yaxis: 'y3'
    };

    const traceVol = {
        x: dates, y: data.volume || [], type: 'bar', name: 'Volume',
        marker: { color: 'rgba(142, 142, 147, 0.5)' }, xaxis: 'x', yaxis: 'y4'
    };

    const layout = {
        autosize: true,
        grid: { rows: 4, columns: 1, pattern: 'independent', roworder: 'top to bottom' },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { family: 'Inter, sans-serif', size: 13 },
        margin: { t: 40, l: 60, r: 30, b: 50 },
        height: 900,
        showlegend: true,
        legend: { orientation: 'h', y: 1.05 },
        hovermode: 'x unified',

        // Axis configuration
        xaxis: { showgrid: false, anchor: 'y4' },
        yaxis: { domain: [0.55, 1], title: 'Price' }, // Main Chart
        yaxis2: { domain: [0.38, 0.50], title: 'RSI', range: [0, 100] }, // RSI
        yaxis3: { domain: [0.20, 0.35], title: 'MACD' }, // MACD
        yaxis4: { domain: [0, 0.15], title: 'Volume' }, // Volume
        
        // Shapes for RSI
        shapes: [
            { type: 'line', xref: 'paper', x0: 0, x1: 1, yref: 'y2', y0: 70, y1: 70, line: { color: 'red', width: 1, dash: 'dot' } },
            { type: 'line', xref: 'paper', x0: 0, x1: 1, yref: 'y2', y0: 30, y1: 30, line: { color: 'green', width: 1, dash: 'dot' } }
        ],
        
        annotations: []
    };

    // --- Add Trade Setup Lines to Chart ---
    if (data.trade_setup) {
        const ts = data.trade_setup;
        const addLine = (y, color, label, dash='solid', width=1) => {
            if (!y || y === 0) return;
            layout.shapes.push({
                type: 'line', xref: 'paper', x0: 0, x1: 1, yref: 'y',
                y0: y, y1: y,
                line: { color: color, width: width, dash: dash }
            });
            layout.annotations.push({
                xref: 'paper', x: 1, yref: 'y', y: y,
                text: `${label} ${y.toFixed(2)}`, showarrow: false,
                font: { color: color, size: 11 }, xanchor: 'left', yanchor: 'middle'
            });
        };

        // Entry, SL, TP
        addLine(ts.entry, '#ffffff', 'Entry', 'dash');
        if (ts.stop_loss) addLine(ts.stop_loss, '#ff4444', 'SL');
        if (ts.target) addLine(ts.target, '#00C851', 'TP');

        // Supports & Resistances (Fainter)
        if (ts.supports) ts.supports.forEach(s => addLine(s, 'rgba(0, 200, 81, 0.3)', '', 'dot'));
        if (ts.resistances) ts.resistances.forEach(r => addLine(r, 'rgba(255, 68, 68, 0.3)', '', 'dot'));
        
        // Increase right margin to fit annotations
        layout.margin.r = 80;
    }

    Plotly.newPlot('main-chart', 
        [traceBBUp, traceBBLow, traceActual, traceSMA, traceTrain, traceTest, traceFuture, traceRSI, traceMACD, traceSignal, traceHist, traceVol], 
        layout, 
        {
            displayModeBar: true, // Enables Home, Reset, Download, etc.
            responsive: true,
            displaylogo: false
        }
    );

    // Force Plotly to resize to full container width immediately
    window.dispatchEvent(new Event('resize'));

    // 3. Report
    // Use marked.js for proper Markdown rendering (handles headers, lists, bolding, etc.)
    const rawReport = data.llama_report || "Report not available.";
    document.getElementById('llama-report').innerHTML = marked.parse(rawReport);
    
    // Reset QA
    document.getElementById('qa-history').innerHTML = '';

    // 4. Stats List
    const statsList = document.getElementById('lstm-stats');
    if (data.lstm_metrics) {
        statsList.innerHTML = `
            <li>RMSE: <strong>${(data.lstm_metrics.rmse || 0).toFixed(2)}</strong></li>
            <li>MAE: <strong>${(data.lstm_metrics.mae || 0).toFixed(2)}</strong></li>
            <li>MAPE: <strong>${(data.lstm_metrics.mape || 0).toFixed(2)}%</strong></li>
            <li>R² Score: <strong>${data.lstm_metrics.r2 !== 'N/A' && data.lstm_metrics.r2 !== undefined ? data.lstm_metrics.r2.toFixed(4) : 'N/A'}</strong></li>
        `;
    } else {
        statsList.innerHTML = '<li>Metrics not available</li>';
    }

    // 8. Classification Metrics
    const rfStats = document.getElementById('rf-stats');
    if (data.rf_metrics) {
        rfStats.innerHTML = `
            <li>Accuracy: <strong>${((data.rf_metrics.accuracy || 0) * 100).toFixed(2)}%</strong></li>
            <li>Precision: <strong>${((data.rf_metrics.precision || 0) * 100).toFixed(2)}%</strong></li>
            <li>Recall: <strong>${((data.rf_metrics.recall || 0) * 100).toFixed(2)}%</strong></li>
            <li>F1 Score: <strong>${((data.rf_metrics.f1_score || 0) * 100).toFixed(2)}%</strong></li>
        `;
    } else {
        rfStats.innerHTML = '<li>Metrics not available</li>';
    }

    // 9. Detailed Class Report
    const reportTable = document.getElementById('class-report-table');
    if (data.rf_metrics && data.rf_metrics.report) {
        const report = data.rf_metrics.report;
        const classes = ['Sell/Hold (0)', 'Buy (1)', 'macro avg', 'weighted avg'];
        reportTable.innerHTML = `
            <thead><tr><th>Class</th><th>Precision</th><th>Recall</th><th>F1-Score</th><th>Support</th></tr></thead>
            <tbody>${classes.map(c => {
                if (!report[c]) return '';
                const r = report[c];
                return `<tr><td>${c}</td><td>${r.precision.toFixed(2)}</td><td>${r.recall.toFixed(2)}</td><td>${r['f1-score'].toFixed(2)}</td><td>${r.support}</td></tr>`;
            }).join('')}</tbody>
        `;
    } else {
        reportTable.innerHTML = '<tr><td style="padding:10px; text-align:center; color:var(--text-secondary);">Detailed report not available.</td></tr>';
    }

    // 5. Feature Importance Chart
    if (data.feat_importance && data.feat_importance.length > 0) {
        const feats = data.feat_importance.slice(0, 5);
        const traceFeat = {
            x: feats.map(f => f.Importance),
            y: feats.map(f => f.Feature),
            type: 'bar', orientation: 'h',
            marker: { color: '#0071e3' }
        };
        Plotly.newPlot('feature-chart', [traceFeat], {
            autosize: true,
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            margin: { t: 20, l: 150, r: 20, b: 30 },
            font: { family: 'Inter, sans-serif', size: 13 },
            yaxis: { automargin: true },
            height: 400
        }, {displayModeBar: false, responsive: true});
    } else {
        document.getElementById('feature-chart').innerHTML = '<p style="text-align:center; padding:20px; color:var(--text-secondary);">Feature importance not available.</p>';
    }
}

// --- QA Logic ---
async function sendQA() {
    const input = document.getElementById('qa-input');
    const question = input.value.trim();
    if (!question || !currentReportData) return;
    
    const history = document.getElementById('qa-history');
    
    // User Msg
    history.innerHTML += `<div class="qa-msg user-msg"><strong>You:</strong> ${question}</div>`;
    input.value = '';
    
    // Loading
    const loadingId = 'qa-loading-' + Date.now();
    history.innerHTML += `<div id="${loadingId}" class="qa-msg ai-msg"><em>Thinking...</em></div>`;
    history.scrollTop = history.scrollHeight;

    try {
        const response = await fetch('/api/qa', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                report_content: currentReportData.llama_report,
                question: question 
            })
        });
        const data = await response.json();
        document.getElementById(loadingId).innerHTML = `<strong>AI:</strong> ${data.answer}`;
    } catch (e) {
        document.getElementById(loadingId).innerHTML = `<strong>Error:</strong> Failed to get answer.`;
    }
}

// --- Report Saving Logic ---
function saveCurrentReport(isAutoSave = false) {
    if (!currentReportData) return;
    
    // Ensure we are saving the latest data structure
    // If config is missing in currentReportData (legacy), it will be saved as missing, which is handled by renderDashboard
    
    const reports = JSON.parse(localStorage.getItem('aarnai_reports') || '[]');
    const newReport = {
        id: Date.now(),
        ticker: currentReportData.ticker,
        date: new Date().toLocaleString(),
        data: currentReportData
    };
    reports.unshift(newReport);
    localStorage.setItem('aarnai_reports', JSON.stringify(reports));
    
    if (!isAutoSave) {
        alert('Report saved successfully!');
    }
    loadReports();
}

function toggleHistory() {
    const el = document.getElementById('history-dropdown');
    el.classList.toggle('hidden');
    if (!el.classList.contains('hidden')) loadReports();
}

function loadReports() {
    const list = document.getElementById('report-list');
    const reports = JSON.parse(localStorage.getItem('aarnai_reports') || '[]');
    
    if (reports.length === 0) {
        list.innerHTML = '<li style="padding:10px; color:#888;">No saved reports.</li>';
        return;
    }
    
    list.innerHTML = reports.map(r => `
        <li class="report-item">
            <div class="report-info" onclick="loadSavedReport(${r.id})">
                <strong>${r.ticker}</strong><br>
                <small>${r.date}</small>
            </div>
            <button class="delete-report-btn" onclick="deleteReport(${r.id}, event)">🗑️</button>
        </li>
    `).join('');
}

function deleteReport(id, event) {
    event.stopPropagation(); // Prevent opening the report when clicking delete
    if (!confirm("Are you sure you want to delete this report?")) return;
    
    let reports = JSON.parse(localStorage.getItem('aarnai_reports') || '[]');
    reports = reports.filter(r => r.id !== id);
    localStorage.setItem('aarnai_reports', JSON.stringify(reports));
    loadReports(); // Refresh list
}

function loadSavedReport(id) {
    const reports = JSON.parse(localStorage.getItem('aarnai_reports') || '[]');
    const report = reports.find(r => r.id === id);
    if (report) {
        currentReportData = report.data;
        try {
            renderDashboard(report.data);
            document.getElementById('dashboard').classList.remove('hidden');
            toggleHistory(); // Close dropdown
        } catch (e) {
            console.error("Error loading report:", e);
            alert("Failed to load this report. It may be from an older version with incompatible data.");
        }
    }
}

// --- Live News Ticker (TV Style) ---
async function startNewsTicker(ticker) {
    const scroll = document.getElementById('tv-news-scroll');
    if (!scroll) return; // Guard clause if element doesn't exist

    scroll.innerHTML = '<div class="tv-news-item">📡 Initializing Global Market Data Streams...</div>';

    try {
        const res = await fetch(`/api/news/${ticker}`);
        const newsData = await res.json();

        // Combine Indian and Global news for ticker
        const allNews = [];
        if (newsData.indian) allNews.push(...newsData.indian);
        if (newsData.global) allNews.push(...newsData.global);

        if (allNews && allNews.length > 0) {
            const items = allNews.map(n => {
                const sentiment = n.sentiment > 0.05 ? '🟢 BULLISH' : (n.sentiment < -0.05 ? '🔴 BEARISH' : '⚪ NEUTRAL');
                return `<div class="tv-news-item"><span>${sentiment}</span> <b>${n.title}</b></div>`;
            }).join('');
            scroll.innerHTML = items;

            // Increased speed: Reduced multiplier from 4 to 1.5
            const duration = Math.max(10, allNews.length * 1.5);
            scroll.style.animationDuration = `${duration}s`;
        } else {
            scroll.innerHTML = `<div class="tv-news-item">No specific headlines found for ${ticker}. Analyzing general market trends...</div>`;
        }
    } catch (e) {
        scroll.innerHTML = '<div class="tv-news-item">⚠️ Live feed unavailable. Continuing internal analysis...</div>';
    }
}

// --- Load Initial News ---
async function loadInitialNews() {
    const newsList = document.getElementById('news-list');
    if (!newsList) return;

    try {
        const res = await fetch('/api/news/NSEI');
        const newsData = await res.json();

        const indianNews = newsData.indian ? newsData.indian.slice(0, 3) : [];
        const globalNews = newsData.global ? newsData.global.slice(0, 3) : [];

        let html = '';

        if (indianNews.length > 0) {
            html += '<h4 style="color: #007aff; margin-bottom: 10px;">🇮🇳 Indian Market News</h4>';
            html += indianNews.map(item => {
                let badgeClass = 'sent-neu';
                let badgeText = 'NEU';
                let emoji = '📰';
                if (item.sentiment > 0.05) { badgeClass = 'sent-pos'; badgeText = 'POS'; emoji = '📈'; }
                else if (item.sentiment < -0.05) { badgeClass = 'sent-neg'; badgeText = 'NEG'; emoji = '📉'; }
                return `<li class="news-item animate__animated animate__fadeInUp">
                    <span class="sentiment-badge ${badgeClass}">${emoji} ${badgeText}</span>
                    <a href="${item.link}" target="_blank">${item.title}</a>
                </li>`;
            }).join('');
        }

        if (globalNews.length > 0) {
            html += '<h4 style="color: #af52de; margin-top: 20px; margin-bottom: 10px;">🌍 Global Finance News</h4>';
            html += globalNews.map(item => {
                let badgeClass = 'sent-neu';
                let badgeText = 'NEU';
                let emoji = '📰';
                if (item.sentiment > 0.05) { badgeClass = 'sent-pos'; badgeText = 'POS'; emoji = '📈'; }
                else if (item.sentiment < -0.05) { badgeClass = 'sent-neg'; badgeText = 'NEG'; emoji = '📉'; }
                return `<li class="news-item animate__animated animate__fadeInUp">
                    <span class="sentiment-badge ${badgeClass}">${emoji} ${badgeText}</span>
                    <a href="${item.link}" target="_blank">${item.title}</a>
                </li>`;
            }).join('');
        }

        if (html) {
            newsList.innerHTML = html;
        } else {
            newsList.innerHTML = '<li class="news-item" style="color:#888;">Loading news...</li>';
        }
    } catch (e) {
        newsList.innerHTML = '<li class="news-item" style="color:#888;">News loading failed.</li>';
    }
}

// --- Show News Modal ---
async function showNewsSection() {
    const ticker = currentReportData ? currentReportData.ticker : 'NSEI'; // Use current ticker or default

    try {
        const res = await fetch(`/api/news/${ticker}`);
        
        // First check if the response is JSON
        const contentType = res.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const errorText = await res.text();
            throw new Error(`Expected JSON but got ${contentType}. Response: ${errorText.substring(0, 200)}...`);
        }
        
        const newsData = await res.json();

        // Create a data object similar to analysis response
        const data = {
            news_items: newsData
        };

        showNewsModal(data);
    } catch (e) {
        console.error("Failed to load news for modal:", e);
        // Show error to user
        const errorMessage = e.message || 'Failed to load news';
        showNotification(`News Error: ${errorMessage}`, 'error');
        
        // Fallback to empty news
        const data = {
            news_items: {
                indian: [],
                global: []
            }
        };
        showNewsModal(data);
    }
}

// --- Professional News Management System ---

// News Analytics State
let newsAnalytics = {
    sentimentHistory: [],
    impactScores: new Map(),
    bookmarkedNews: new Set(),
    newsFilters: {
        sentiment: 'all',
        region: 'all',
        sector: 'all',
        impact: 'all'
    },
    realTimeUpdates: true,
    notificationSettings: {
        breaking: true,
        highImpact: true,
        portfolioRelated: true
    }
};

// Feature 1: Advanced Sentiment Analysis with Visual Indicators
function calculateAdvancedSentiment(item) {
    const baseSentiment = item.sentiment || 0;
    const title = item.title.toLowerCase();
    const content = item.content || item.title;

    // Keyword-based sentiment enhancement
    const positiveKeywords = ['surge', 'rally', 'gains', 'profit', 'growth', 'bullish', 'upgrade', 'beat'];
    const negativeKeywords = ['plunge', 'crash', 'losses', 'decline', 'bearish', 'downgrade', 'miss'];

    let enhancedSentiment = baseSentiment;
    positiveKeywords.forEach(keyword => {
        if (title.includes(keyword)) enhancedSentiment += 0.1;
    });
    negativeKeywords.forEach(keyword => {
        if (title.includes(keyword)) enhancedSentiment -= 0.1;
    });

    return Math.max(-1, Math.min(1, enhancedSentiment));
}

// Feature 2: Impact Scoring System
function calculateImpactScore(item, ticker) {
    let score = 0;
    const title = item.title.toLowerCase();

    // Company-specific impact
    if (ticker && title.includes(ticker.toLowerCase())) score += 50;

    // Market-wide impact keywords
    const highImpactKeywords = ['fed', 'central bank', 'government', 'policy', 'regulation', 'economy'];
    const mediumImpactKeywords = ['earnings', 'quarterly', 'merger', 'acquisition', 'dividend'];

    highImpactKeywords.forEach(keyword => {
        if (title.includes(keyword)) score += 30;
    });
    mediumImpactKeywords.forEach(keyword => {
        if (title.includes(keyword)) score += 15;
    });

    // Sentiment magnitude
    score += Math.abs(item.sentiment || 0) * 20;

    return Math.min(100, score);
}

// Feature 3: News Categorization by Sector
function categorizeNewsBySector(item) {
    const title = item.title.toLowerCase();
    const sectors = {
        'Technology': ['tech', 'software', 'ai', 'digital', 'cyber', 'cloud', 'semiconductor'],
        'Finance': ['bank', 'financial', 'insurance', 'investment', 'capital'],
        'Healthcare': ['pharma', 'medical', 'health', 'biotech', 'drug'],
        'Energy': ['oil', 'gas', 'energy', 'renewable', 'solar', 'wind'],
        'Consumer': ['retail', 'consumer', 'automotive', 'luxury', 'food'],
        'Industrial': ['industrial', 'manufacturing', 'construction', 'mining'],
        'Real Estate': ['real estate', 'property', 'housing', 'commercial']
    };

    for (const [sector, keywords] of Object.entries(sectors)) {
        if (keywords.some(keyword => title.includes(keyword))) {
            return sector;
        }
    }
    return 'General';
}

// Feature 4: Real-time News Updates with WebSocket Simulation
function initializeRealTimeNews() {
    if (!newsAnalytics.realTimeUpdates) return;

    // Simulate real-time updates every 30 seconds
    setInterval(async () => {
        try {
            const response = await fetch('/api/news/NSEI');
            const newData = await response.json();

            // Check for new breaking news
            const newItems = [...(newData.indian || []), ...(newData.global || [])];
            const breakingNews = newItems.filter(item => {
                const impact = calculateImpactScore(item);
                return impact > 70 && !newsAnalytics.impactScores.has(item.title);
            });

            if (breakingNews.length > 0 && newsAnalytics.notificationSettings.breaking) {
                showBreakingNewsAlert(breakingNews[0]);
            }

            // Update analytics
            newItems.forEach(item => {
                newsAnalytics.impactScores.set(item.title, calculateImpactScore(item));
            });

        } catch (e) {
            console.log('Real-time news update failed:', e);
        }
    }, 30000);
}

// Feature 5: Breaking News Alert System
function showBreakingNewsAlert(newsItem) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'breaking-news-alert';
    alertDiv.innerHTML = `
        <div class="breaking-header">🚨 BREAKING NEWS</div>
        <div class="breaking-content">${newsItem.title}</div>
        <button onclick="this.parentElement.remove()">×</button>
    `;
    alertDiv.onclick = () => {
        showNewsModal({ news_items: { indian: [newsItem], global: [] } });
        alertDiv.remove();
    };

    document.body.appendChild(alertDiv);

    // Auto-remove after 10 seconds
    setTimeout(() => {
        if (alertDiv.parentElement) alertDiv.remove();
    }, 10000);
}

// Feature 6: News Bookmarking System
function toggleBookmark(newsTitle) {
    if (newsAnalytics.bookmarkedNews.has(newsTitle)) {
        newsAnalytics.bookmarkedNews.delete(newsTitle);
        return false;
    } else {
        newsAnalytics.bookmarkedNews.add(newsTitle);
        return true;
    }
}

// Feature 7: Advanced News Filtering
function applyNewsFilters(newsItems) {
    return newsItems.filter(item => {
        const sentiment = calculateAdvancedSentiment(item);
        const region = item.region || 'global';
        const sector = categorizeNewsBySector(item);
        const impact = calculateImpactScore(item);

        // Sentiment filter
        if (newsAnalytics.newsFilters.sentiment !== 'all') {
            if (newsAnalytics.newsFilters.sentiment === 'positive' && sentiment <= 0.05) return false;
            if (newsAnalytics.newsFilters.sentiment === 'negative' && sentiment >= -0.05) return false;
            if (newsAnalytics.newsFilters.sentiment === 'neutral' && Math.abs(sentiment) > 0.05) return false;
        }

        // Region filter
        if (newsAnalytics.newsFilters.region !== 'all' && region !== newsAnalytics.newsFilters.region) return false;

        // Sector filter
        if (newsAnalytics.newsFilters.sector !== 'all' && sector !== newsAnalytics.newsFilters.sector) return false;

        // Impact filter
        if (newsAnalytics.newsFilters.impact !== 'all') {
            if (newsAnalytics.newsFilters.impact === 'high' && impact < 50) return false;
            if (newsAnalytics.newsFilters.impact === 'medium' && (impact < 25 || impact >= 50)) return false;
            if (newsAnalytics.newsFilters.impact === 'low' && impact >= 25) return false;
        }

        return true;
    });
}

// Feature 8: News Analytics Dashboard
function renderNewsAnalytics() {
    const analytics = calculateNewsAnalytics();
    return `
        <div class="news-analytics">
            <div class="analytics-metric">
                <span class="metric-label">Total News Items</span>
                <span class="metric-value">${analytics.totalItems}</span>
            </div>
            <div class="analytics-metric">
                <span class="metric-label">Positive Sentiment</span>
                <span class="metric-value">${analytics.positivePercentage}%</span>
            </div>
            <div class="analytics-metric">
                <span class="metric-label">High Impact News</span>
                <span class="metric-value">${analytics.highImpactCount}</span>
            </div>
            <div class="analytics-metric">
                <span class="metric-label">Bookmarked</span>
                <span class="metric-value">${newsAnalytics.bookmarkedNews.size}</span>
            </div>
        </div>
    `;
}

function calculateNewsAnalytics() {
    // This would be calculated from actual news data
    return {
        totalItems: 150,
        positivePercentage: 45,
        highImpactCount: 12,
        trendingTopics: ['Technology', 'Finance', 'Healthcare']
    };
}

// Feature 9: News Search with Advanced Filters
function searchNews(query, filters = {}) {
    // Implement fuzzy search with filters
    const searchTerm = query.toLowerCase();
    // This would search through cached news items
    return []; // Placeholder
}

// Feature 10: News Timeline Visualization
function renderNewsTimeline(newsItems) {
    const timeline = newsItems
        .sort((a, b) => new Date(b.publishedAt || 0) - new Date(a.publishedAt || 0))
        .map(item => {
            const time = new Date(item.publishedAt).toLocaleTimeString();
            return `<div class="timeline-item">
                <div class="timeline-time">${time}</div>
                <div class="timeline-content">${item.title}</div>
            </div>`;
        }).join('');

    return `<div class="news-timeline">${timeline}</div>`;
}

// Feature 11: Social Sentiment Integration (Mock)
function getSocialSentiment(symbol) {
    // Mock social sentiment data
    return {
        twitter: Math.random() * 2 - 1,
        reddit: Math.random() * 2 - 1,
        overall: Math.random() * 2 - 1
    };
}

// Feature 12: News Impact Prediction
function predictNewsImpact(item) {
    const impact = calculateImpactScore(item);
    const sentiment = calculateAdvancedSentiment(item);

    // Simple prediction model
    const predictedVolatility = Math.abs(sentiment) * impact / 100;
    const predictedDirection = sentiment > 0 ? 'bullish' : 'bearish';

    return {
        volatility: predictedVolatility,
        direction: predictedDirection,
        confidence: Math.min(0.9, impact / 100)
    };
}

// Feature 13: Personalized News Feed
function generatePersonalizedNews(portfolio = []) {
    // Filter news based on portfolio holdings
    // This would analyze which companies are in user's portfolio
    return []; // Placeholder
}

// Feature 14: News Summary Generation
function generateNewsSummary(newsItems) {
    const positive = newsItems.filter(item => item.sentiment > 0.05).length;
    const negative = newsItems.filter(item => item.sentiment < -0.05).length;
    const neutral = newsItems.length - positive - negative;

    return {
        summary: `Market sentiment shows ${positive} positive, ${negative} negative, and ${neutral} neutral news items.`,
        trend: positive > negative ? 'bullish' : negative > positive ? 'bearish' : 'neutral',
        keyTopics: ['Technology', 'Finance'] // Would be calculated
    };
}

// Feature 15: News Comparison Tools
function compareNewsSources() {
    // Compare sentiment across different news sources
    return {
        'Reuters': { positive: 65, negative: 35 },
        'Bloomberg': { positive: 55, negative: 45 },
        'CNBC': { positive: 70, negative: 30 }
    };
}

// Feature 16: News Notification Preferences
function updateNotificationSettings(settings) {
    newsAnalytics.notificationSettings = { ...newsAnalytics.notificationSettings, ...settings };
    localStorage.setItem('newsNotifications', JSON.stringify(newsAnalytics.notificationSettings));
}

// Feature 17: News Archiving System
function archiveNews(newsItem) {
    const archives = JSON.parse(localStorage.getItem('newsArchives') || '[]');
    archives.push({
        ...newsItem,
        archivedAt: new Date().toISOString()
    });
    localStorage.setItem('newsArchives', JSON.stringify(archives));
}

// Feature 18: News Export Functionality
function exportNewsData(format = 'json') {
    const newsData = {
        items: [], // Would contain current news items
        analytics: calculateNewsAnalytics(),
        exportedAt: new Date().toISOString()
    };

    if (format === 'csv') {
        // Convert to CSV format
        return 'Title,Sentiment,Impact,Date\n' + newsData.items.map(item =>
            `"${item.title}",${item.sentiment},${calculateImpactScore(item)},"${item.publishedAt}"`
        ).join('\n');
    }

    return JSON.stringify(newsData, null, 2);
}

// Feature 19: News Clustering by Topics
function clusterNewsByTopics(newsItems) {
    const clusters = {};
    newsItems.forEach(item => {
        const topic = categorizeNewsBySector(item);
        if (!clusters[topic]) clusters[topic] = [];
        clusters[topic].push(item);
    });
    return clusters;
}

// Feature 20: Advanced News Visualization
function renderNewsVisualization(newsItems) {
    const sentimentData = newsItems.map(item => ({
        title: item.title.substring(0, 30) + '...',
        sentiment: calculateAdvancedSentiment(item),
        impact: calculateImpactScore(item)
    }));

    // This would create charts showing sentiment distribution, impact levels, etc.
    return sentimentData;
}

// --- Enhanced Show News Modal Function ---
function showNewsModal(data) {
    const modal = document.getElementById('news-modal');
    const newsList = document.getElementById('modal-news-list');
    if (!modal || !newsList) return;

    // Initialize real-time updates if not already done
    if (!window.newsRealTimeInitialized) {
        initializeRealTimeNews();
        window.newsRealTimeInitialized = true;
    }

    if (data.news_items && data.news_items.indian && data.news_items.global) {
        let allNews = [...(data.news_items.indian || []), ...(data.news_items.global || [])];

        // Apply filters
        allNews = applyNewsFilters(allNews);

        // Sort by impact score
        allNews.sort((a, b) => calculateImpactScore(b) - calculateImpactScore(a));

        const indianNews = allNews.filter(item => item.region === 'indian').slice(0, 15);
        const globalNews = allNews.filter(item => item.region !== 'indian').slice(0, 15);

        let html = '';

        // News Analytics Header
        html += renderNewsAnalytics();

        // Filter Controls
        html += `
            <div class="news-filters">
                <select id="sentiment-filter" onchange="updateNewsFilter('sentiment', this.value)">
                    <option value="all">All Sentiment</option>
                    <option value="positive">Positive</option>
                    <option value="negative">Negative</option>
                    <option value="neutral">Neutral</option>
                </select>
                <select id="impact-filter" onchange="updateNewsFilter('impact', this.value)">
                    <option value="all">All Impact</option>
                    <option value="high">High Impact</option>
                    <option value="medium">Medium Impact</option>
                    <option value="low">Low Impact</option>
                </select>
                <button onclick="exportNewsData('csv')" class="export-btn">📊 Export</button>
            </div>
        `;

        if (indianNews.length > 0) {
            html += '<h4 style="color: #007aff; margin: 20px 0 10px 0;">🇮🇳 Indian Market News</h4>';
            html += indianNews.map(item => renderProfessionalNewsItem(item, 'indian')).join('');
        }

        if (globalNews.length > 0) {
            html += '<h4 style="color: #af52de; margin: 20px 0 10px 0;">🌍 Global Finance News</h4>';
            html += globalNews.map(item => renderProfessionalNewsItem(item, 'global')).join('');
        }

        if (html) {
            newsList.innerHTML = html;
        } else {
            newsList.innerHTML = '<li class="news-item" style="color:#888;">No news matches your filters.</li>';
        }
    } else {
        newsList.innerHTML = '<li class="news-item" style="color:#888;">No recent news found.</li>';
    }

    modal.classList.remove('hidden');
}

// Professional News Item Renderer
function renderProfessionalNewsItem(item, region) {
    const sentiment = calculateAdvancedSentiment(item);
    const impact = calculateImpactScore(item, currentReportData?.ticker);
    const sector = categorizeNewsBySector(item);
    const prediction = predictNewsImpact(item);
    const isBookmarked = newsAnalytics.bookmarkedNews.has(item.title);

    let badgeClass = 'sent-neu';
    let badgeText = 'NEUTRAL';
    let emoji = '📰';
    let impactColor = '#888';

    if (sentiment > 0.1) { badgeClass = 'sent-pos'; badgeText = 'BULLISH'; emoji = '📈'; }
    else if (sentiment < -0.1) { badgeClass = 'sent-neg'; badgeText = 'BEARISH'; emoji = '📉'; }

    if (impact > 70) impactColor = '#ff4444';
    else if (impact > 40) impactColor = '#ffaa00';
    else if (impact > 20) impactColor = '#00aa44';

    const imageUrl = `data:image/svg+xml;base64,${btoa(`<svg width="80" height="60" xmlns="http://www.w3.org/2000/svg"><rect width="80" height="60" fill="#f0f0f0"/><text x="40" y="35" font-family="Arial" font-size="10" fill="#666" text-anchor="middle">${sector}</text></svg>`)}`;

    return `
        <li class="news-item professional" data-impact="${impact}" data-sentiment="${sentiment}">
            <img src="${imageUrl}" alt="News Image" loading="lazy" style="width: 80px; height: 60px; object-fit: cover; border-radius: 8px; margin-right: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <div style="flex: 1;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <div>
                        <span class="sentiment-badge ${badgeClass}">${emoji} ${badgeText}</span>
                        <span class="sector-badge" style="background: ${region === 'indian' ? '#007aff' : '#af52de'}; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; margin-left: 8px;">${sector}</span>
                    </div>
                    <div style="display: flex; gap: 8px; align-items: center;">
                        <span class="impact-score" style="color: ${impactColor}; font-weight: bold; font-size: 12px;">${impact.toFixed(0)}%</span>
                        <button onclick="toggleBookmark('${item.title.replace(/'/g, "\\'")}')" class="bookmark-btn" style="background: none; border: none; cursor: pointer; font-size: 16px;">
                            ${isBookmarked ? '⭐' : '☆'}
                        </button>
                    </div>
                </div>
                <a href="${item.link}" target="_blank" style="display: block; color: inherit; text-decoration: none; font-weight: 500; line-height: 1.4; margin-bottom: 4px;">${item.title}</a>
                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 11px; color: #666;">
                    <span>${item.source || 'Unknown Source'} • ${new Date(item.publishedAt || Date.now()).toLocaleString()}</span>
                    <div>
                        <span style="color: ${prediction.direction === 'bullish' ? '#00C851' : '#ff4444'};">
                            ${prediction.direction.toUpperCase()} (${(prediction.confidence * 100).toFixed(0)}%)
                        </span>
                    </div>
                </div>
            </div>
        </li>
    `;
}

// Filter update function
function updateNewsFilter(type, value) {
    newsAnalytics.newsFilters[type] = value;
    // Re-render modal with new filters
    if (currentReportData) {
        showNewsModal(currentReportData);
    }
}

// --- Close News Modal ---
function closeNewsModal() {
    const modal = document.getElementById('news-modal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

// --- Downloads ---
function downloadCSV() {
    if (!currentReportData) return;
    const data = currentReportData;

    // Create CSV content (Dates, Actual, Train, Test, Future)
    // This is a simplified export. For full export, backend should handle it or we construct a large CSV here.
    // Let's export the Future Forecast as a simple example
    let csvContent = "data:text/csv;charset=utf-8,Date,Predicted Close\n";
    data.future_dates.forEach((d, i) => {
        csvContent += `${d},${data.future_preds[i]}\n`;
    });

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `${data.ticker}_forecast.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

async function downloadPDF() {
    if (!currentReportData) return;
    try {
        const response = await fetch('/generate_pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                report_content: currentReportData.llama_report,
                ticker: currentReportData.ticker,
                fundamentals: currentReportData.fundamentals
            })
        });
        const blob = await response.json();
        const link = document.createElement('a');
        link.href = `data:application/pdf;base64,${blob.pdf_base64}`;
        link.download = `${currentReportData.ticker}_report.pdf`;
        link.click();
    }
    catch (e) {alert("PDF Generation failed: " + e.message);
        }
    }