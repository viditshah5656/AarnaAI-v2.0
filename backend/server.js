
const express = require('express');
const cors = require('cors');
const yahooFinance = require('yahoo-finance2').default;
const technicalIndicators = require('technicalindicators');
const Sentiment = require('sentiment');

const app = express();
const port = 3001; // We'''ll run the backend on a different port from the frontend
const sentiment = new Sentiment();

app.use(cors());
app.use(express.json());

// A simple cache to avoid spamming the Yahoo Finance API
const cache = {};
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

async function getQuote(symbol) {
    const now = Date.now();
    if (cache[symbol] && (now - cache[symbol].timestamp) < CACHE_TTL) {
        return cache[symbol].data;
    }

    try {
        const queryOptions = {
            period1: '2023-01-01', // Get a good range of data
            interval: '1d',
        };
        const [quote, news] = await Promise.all([
            yahooFinance.chart(symbol, queryOptions),
            yahooFinance.search(symbol, { newsCount: 20 })
        ]);

        const data = { quote, news: news.news };
        cache[symbol] = { timestamp: now, data };
        return data;
    } catch (error) {
        console.error(`Error fetching data for ${symbol}:`, error);
        throw new Error('Failed to fetch data from Yahoo Finance API');
    }
}


// Endpoint to get core chart data
app.get('/api/data/:symbol', async (req, res) => {
    try {
        const { symbol } = req.params;
        const { quote } = await getQuote(symbol);
        res.json(quote);
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
});

// Endpoint to get news
app.get('/api/news/:symbol', async (req, res) => {
    try {
        const { symbol } = req.params;
        const { news } = await getQuote(symbol);
        res.json(news);
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
});


// Endpoint for sentiment analysis
app.get('/api/sentiment/:symbol', async (req, res) => {
    try {
        const { symbol } = req.params;
        const { news } = await getQuote(symbol);
        
        if (!news || news.length === 0) {
            return res.json({ score: 0, comparative: 0, positive: [], negative: [] });
        }

        const headlines = news.map(item => item.title).join(' ');
        const result = sentiment.analyze(headlines);
        res.json(result);

    } catch (error) {
        res.status(500).json({ message: error.message });
    }
});

// Endpoint for technical indicators
app.get('/api/indicators/:symbol', async (req, res) => {
    try {
        const { symbol } = req.params;
        const { quote } = await getQuote(symbol);
        const closePrices = quote.quotes.map(q => q.close);

        if (closePrices.length === 0) {
            return res.json({});
        }

        const sma = technicalIndicators.sma({ period: 20, values: closePrices }).slice(-1)[0];
        const ema = technicalIndicators.ema({ period: 20, values: closePrices }).slice(-1)[0];
        const rsi = technicalIndicators.rsi({ period: 14, values: closePrices }).slice(-1)[0];
        const macdInput = {
            values: closePrices,
            fastPeriod: 12,
            slowPeriod: 26,
            signalPeriod: 9,
            SimpleMAOscillator: false,
            SimpleMASignal: false
        };
        const macd = technicalIndicators.macd(macdInput).slice(-1)[0];

        res.json({ sma, ema, rsi, macd });

    } catch (error) {
        res.status(500).json({ message: error.message });
    }
});


app.listen(port, () => {
    console.log(`Aarna AI Backend running at http://localhost:${port}`);
});
