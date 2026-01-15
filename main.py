# ======================================================
# LOAD ALL COMPONENTS
# ======================================================

# Load environment variables first
from dotenv import load_dotenv
import os

# Print current working directory and list files
print("Current working directory:", os.getcwd())
print("Files in directory:", os.listdir('.'))

# Try to load .env file with explicit path
env_path = os.path.join(os.path.dirname(__file__), '.env')
print(f"Loading .env file from: {env_path}")
load_dotenv(env_path)

# Debug: Print environment variables
print("Environment variables loaded:")
for key in ['GROQ_API_KEY', 'ALPHA_VANTAGE_API_KEY', 'NEWSAPI_API_KEY']:
    value = os.getenv(key)
    print(f"{key}: {'*****' + value[-4:] if value else 'Not found'}")

# Early TensorFlow environment configuration
import os
import warnings
import logging

os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_GPU_ALLOCATOR'] = 'cuda_malloc_async'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
warnings.filterwarnings('ignore')

logging.getLogger('requests').setLevel(logging.ERROR)
logging.getLogger('urllib3').setLevel(logging.ERROR)
logging.getLogger('yahooquery').setLevel(logging.ERROR)
logging.getLogger('yfinance').setLevel(logging.ERROR)
logging.getLogger('tensorflow').setLevel(logging.ERROR)

# Consolidated imports
import gc
import threading
import multiprocessing
import math
import time
import datetime
import base64
import re
import json
import argparse
import sys
import traceback
from typing import Any, Dict, List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from numpy.typing import NDArray

import tensorflow as tf
import tensorflow_probability as tfp
from tensorflow_probability import layers as tfpl
from tensorflow.keras.layers import Dense, LSTM, Dropout, Input, Bidirectional, BatchNormalization, MultiHeadAttention
import keras_tuner as kt
import pywt

import pandas as pd
import numpy as np
import requests
import yfinance as yf
from sklearn.linear_model import LinearRegression
from sklearn.mixture import GaussianMixture
from sklearn.ensemble import RandomForestClassifier, VotingClassifier, ExtraTreesClassifier, HistGradientBoostingClassifier
from sklearn.base import BaseEstimator
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, mean_squared_error, mean_absolute_error,
    classification_report, confusion_matrix, precision_recall_curve, r2_score
)
from sklearn.mixture import GaussianMixture
from sklearn.ensemble import RandomForestClassifier, VotingClassifier, ExtraTreesClassifier, HistGradientBoostingClassifier
from sklearn.base import BaseEstimator
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, mean_squared_error, mean_absolute_error, 
    classification_report, confusion_matrix, precision_recall_curve, r2_score
)
from sklearn.calibration import CalibratedClassifierCV
from sklearn.preprocessing import RobustScaler
import scipy.optimize as sco

# Visualization
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# NLP & Text
import nltk

# FastAPI
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as redis
from typing import Optional
import os
from pathlib import Path
import logging
from datetime import datetime, timedelta
import json
import hashlib
import secrets
from pydantic import BaseModel
import csv


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AarnaAI Stock Prediction API",
    description="Advanced AI-powered stock prediction and analysis platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Security
security = HTTPBearer()

# Rate limiting
redis_client = redis.from_url("redis://localhost:6379", encoding="utf-8", decode_responses=True)
FastAPILimiter.init(redis_client)

# CORS configuration
origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "https://yourdomain.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    csp_policy = """
        default-src 'self';
        script-src 'self' 'unsafe-inline' 'unsafe-eval' cdn.plot.ly cdn.jsdelivr.net;
        script-src-elem 'self' 'unsafe-inline' cdn.plot.ly cdn.jsdelivr.net;
        style-src 'self' 'unsafe-inline' fonts.googleapis.com;
        style-src-elem 'self' 'unsafe-inline' fonts.googleapis.com;
        font-src 'self' data: fonts.gstatic.com;
        img-src 'self' data: https: blob:;
        connect-src 'self' *.googleapis.com *.jsdelivr.net cdn.plot.ly;
        frame-ancestors 'none';
    """.replace('\n', ' ').strip()
    response.headers["Content-Security-Policy"] = csp_policy
    return response

@app.get('/api/tickers')
async def get_tickers():
    try:
        # Use absolute path to tickers.csv
        base_dir = os.path.dirname(os.path.abspath(__file__))
        tickers_path = os.path.join(base_dir, 'tickers.csv')
        
        # Fallback to static directory if not found in root
        if not os.path.exists(tickers_path):
            tickers_path = os.path.join(base_dir, 'static', 'tickers.csv')
            
        tickers = []
        with open(tickers_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            # Skip header if exists
            next(reader, None)
            tickers = [row[0].strip() for row in reader if row and row[0].strip()]
            
        if not tickers:
            # Return a default set of tickers if the file is empty or invalid
            tickers = ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'HINDUNILVR.NS']
            
        return {"tickers": tickers}
    except Exception as e:
        logger.error(f"Error loading tickers: {str(e)}")
        # Return default tickers even if there's an error
        return {"tickers": ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'HINDUNILVR.NS']}

# Error handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

# API key validation
async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    api_key = credentials.credentials
    # In production, validate against a database or secure storage
    valid_keys = ["your-secure-api-key"]  # Replace with actual key validation
    if api_key not in valid_keys:
        raise HTTPException(
            status_code=401,
            detail="Invalid API Key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return api_key

# TensorFlow environment configured above; now configure GPU if available
# GPU and TensorFlow configuration - Prefer GPU but allow CPU fallback
gpus = tf.config.list_physical_devices('GPU')
if gpus:
    print(f"[INFO] GPU(s) detected: {len(gpus)} device(s)")
    for gpu in gpus:
        tf.config.experimental.set_memory_growth(gpu, True)
    tf.config.optimizer.set_jit(True)
    from keras import mixed_precision
    mixed_precision.set_global_policy('mixed_float16')
    print("[INFO] TensorFlow configured for GPU execution with mixed_float16 precision.")
else:
    pass

# ======================================================
# AI TUNING SAFETY GUARD (ONE-SHOT)
# ======================================================
AI_TUNING_USED = False

# --- THREAD-SAFE PROGRESS TRACKING ---
progress_lock = threading.Lock()

# --- GLOBAL EXECUTORS ---
io_executor = ThreadPoolExecutor(max_workers=20, thread_name_prefix='IO_bound')



# Optimize CPU parallelism for Scikit-Learn / OpenMP
os.environ['OMP_NUM_THREADS'] = str(multiprocessing.cpu_count())

# Optimization: Intel Extension for Scikit-learn (if available)
# Disabled to prevent OpenMP/oneDNN conflicts with TensorFlow causing hangs
# try:
#     from sklearnex import patch_sklearn
#     patch_sklearn()
# except ImportError:
#     pass


# Global definition of columns to drop to ensure consistency between Training and Inference
COLS_TO_DROP = [
    "Signal", "Signal_Line", 'Ticker', 'TR', 'Adj Close', 'Open', 'High', 'Low', 'Close', 'Return', 
    'Middle_BB', 'Std_BB', 'SMA50', 'UpMove', 'DownMove', 'PlusDM', 'MinusDM', 
    'TR_Smooth', 'PlusDM_Smooth', 'MinusDM_Smooth', 'PlusDI', 'MinusDI', 'DX',
    'Sum_TR', 'Range_HL']

# ======================================================
# Basic setup
# ======================================================
warnings.filterwarnings('ignore')
tf.get_logger().setLevel('ERROR')

# Global storage for training progress
training_progress = {}

# --- INSTITUTIONAL MODEL REGISTRY ---
# Stores the 'Champion' model metrics for each ticker to prevent performance regression
MODEL_REGISTRY = {}
registry_lock = threading.Lock()

# --- ACCOUNT & RISK MANAGEMENT (Kill-Switch) ---
ACCOUNT = {
    "initial_capital": 1_000_000.0,
    "current_value": 1_000_000.0,
    "daily_initial_value": 1_000_000.0,
    "last_reset_date": None,
    "kill_switch_active": False,
    "daily_drawdown_limit": 0.02
}
account_lock = threading.Lock()

def check_account_kill_switch():
    """
    Checks and updates the daily account kill-switch.
    In a real system, ACCOUNT['current_value'] would be updated by a separate portfolio manager.
    Here, we simulate the check based on the global state.
    """
    with account_lock:
        today = datetime.date.today()
        if ACCOUNT["last_reset_date"] != today:
            ACCOUNT["last_reset_date"] = today
            ACCOUNT["daily_initial_value"] = ACCOUNT["current_value"]
            ACCOUNT["kill_switch_active"] = False

        daily_drawdown = (ACCOUNT["daily_initial_value"] - ACCOUNT["current_value"]) / ACCOUNT["daily_initial_value"]
        
        if daily_drawdown > ACCOUNT["daily_drawdown_limit"]:

            # Set up logger
            logger = logging.getLogger("aarnaai")
            logger.setLevel(logging.INFO)
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logger.addHandler(handler)

            # Global state with thread-safe storage
            app.state.cache = {}
            app.state.last_updated = datetime.now()
            app.state.market_status = "CLOSED"
            app.state.system_health = {
                "api_health": "HEALTHY",
                "model_health": "HEALTHY",
                "database_health": "HEALTHY",
                "last_checked": datetime.now().isoformat(),
                "version": "1.0.0",
                "uptime": datetime.now().isoformat(),
                "memory_usage": "N/A",
                "cpu_usage": "N/A"
            }

            # Rate limiting configuration
            RATE_LIMIT = "100/minute"

# Health check endpoint
@app.get("/api/health", response_model=dict)
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

# Get absolute path to static directory to ensure correct resolution regardless of CWD
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Serve static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Serve the main application
@app.get("/")
async def read_root():
    return FileResponse(os.path.join(STATIC_DIR, 'analysis.html'))

# Serve the analysis page
@app.get("/analysis")
async def analysis_page():
    return FileResponse(os.path.join(STATIC_DIR, 'analysis.html'))

# Catch-all route for frontend routing - must be the last route
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    # Try to serve the requested file if it exists
    file_path = os.path.join(STATIC_DIR, full_path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    # Otherwise serve analysis.html for frontend routing
    return FileResponse(os.path.join(STATIC_DIR, 'index.html'))

# ======================================================
# Utilities
# ======================================================
def get_rounded_time(minutes=15):
    """Helper for TTL-like caching with lru_cache."""
    return round(time.time() / (minutes * 60))


def make_columns_unique(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ['_'.join([str(i) for i in col if i]).strip('_') for col in df.columns]
    cols = df.columns.tolist()
    unique_cols = []
    for col in cols:
        if col in unique_cols:
            i = 1
            while f"{col}_{i}" in unique_cols:
                i += 1
            unique_cols.append(f"{col}_{i}")
        else:
            unique_cols.append(col)
    df.columns = unique_cols
    return df

def df_to_csv_download_link(df: pd.DataFrame, filename="export.csv", label="Download CSV"):
    csv = df.to_csv(index=True)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{label}</a>'
    return href

def make_csv_download_button(df: pd.DataFrame, filename: str, label: str):
    import streamlit as st
    try:
        csv_bytes = df.to_csv(index=True).encode('utf-8')
        st.download_button(label, data=csv_bytes, file_name=filename, mime="text/csv")
    except Exception:
        st.markdown(df_to_csv_download_link(df, filename=filename, label=label), unsafe_allow_html=True)

def normalize_ticker(ticker: str) -> str:
    if not ticker:
        return ticker

    ticker = ticker.strip().upper()

    # Allow indices as-is
    if ticker.startswith("^"):
        return ticker

    # Already valid
    if ticker.endswith((".NS", ".BO")):
        return ticker

    # Default NSE
    return ticker + ".NS"

def _fetch_and_process_yf_data(ticker: str, period: str, interval: str) -> pd.DataFrame:
    """Internal helper to fetch and process data for a given ticker."""
    try:
        t = Ticker(ticker)
        df = t.history(
            period=period,
            interval=interval
        )

        if df is None or df.empty:
            # Ticker.history is the primary method, no fallback needed
            return pd.DataFrame()

        if df is None or df.empty:
            return pd.DataFrame()

        # Flatten columns if they are MultiIndex
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [
                "_".join([str(i) for i in col if i]).strip("_")
                for col in df.columns
            ]

        # Standardize column names
        rename = {}
        for c in df.columns:
            cl = c.lower()
            if "open" in cl: rename[c] = "Open"
            elif "high" in cl: rename[c] = "High"
            elif "low" in cl: rename[c] = "Low"
            elif "close" in cl and 'adj' not in cl: rename[c] = "Close"
            elif "volume" in cl: rename[c] = "Volume"

        df = df.rename(columns=rename)

        # Ensure essential columns exist
        needed = ["Open", "High", "Low", "Close", "Volume"]
        # Some tickers might not have Volume, so we only keep what's available
        df = df[[c for c in needed if c in df.columns]]

        df = df.dropna(subset=["Open", "High", "Low", "Close"])
        df.index = pd.to_datetime(df.index)

        return df

    except Exception:
        # If any step fails, return an empty DataFrame
        return pd.DataFrame()

# --- EMBEDDING & SENTIMENT UTILITIES ---
embedding_model = None

def get_top_market_news(limit=25):
    """
    Fetch top Indian market-wide financial news (focused on Indian shares).
    """
    try:
        url = "https://query1.finance.yahoo.com/v1/finance/news"
        params = {
            "category": "generalnews",
            "region": "IN",
            "lang": "en-US"
        }

        r = requests.get(url, params=params, timeout=5)
        data = r.json()

        articles = data.get("items", {}).get("result", [])
        headlines = []

        for a in articles:
            title = a.get("title")
            if title and ("India" in title or "NSE" in title or "BSE" in title or "Indian" in title):
                headlines.append(title)

        # If not enough Indian news, add general
        if len(headlines) < limit:
            for a in articles:
                title = a.get("title")
                if title and title not in headlines:
                    headlines.append(title)

        return headlines[:limit]

    except Exception:
        return []

@lru_cache(maxsize=4)
def get_news_embeddings(_ticker: str = "MARKET"):
    """
    Generates embeddings for top market-wide news.
    Ticker is ignored intentionally.
    """
    global embedding_model

    if SentenceTransformer is None:
        return None

    if embedding_model is None:
        try:
            embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception:
            return None

    # =========================
    # FETCH TOP MARKET NEWS
    # =========================
    titles = get_top_market_news()

    if not titles:
        return None

    embeddings = embedding_model.encode(titles, convert_to_tensor=False)

    today = pd.to_datetime(datetime.date.today())

    emb_df = pd.DataFrame(
        [np.mean(embeddings, axis=0)],
        index=[today]
    )

    emb_df.columns = [f"emb_{i}" for i in range(emb_df.shape[1])]
    return emb_df

@lru_cache(maxsize=2)
def read_tickers(csv_path=None):
    try:
        if csv_path is None:
            csv_path = os.path.join(BASE_DIR, "tickers.csv")

        df = pd.read_csv(csv_path, skipinitialspace=True, usecols=[0])
        col = df.columns[0]
        
        tickers = df[col].dropna().astype(str).str.strip().tolist()
        tickers = [t for t in tickers if t and t.upper() != 'SYMBOL']  # Remove empty and header
        return tickers

    except Exception as e:
        print("❌ read_tickers failed:", e)
        return []


from yahooquery import Ticker

@lru_cache(maxsize=32)
def safe_load_data(ticker: str, period: str = "1y", interval: str = "1d", max_retries: int = 3) -> pd.DataFrame:
    """Robust data loading with retries and fallback mechanisms.
    
    Args:
        ticker: Stock ticker symbol
        period: Data period to fetch (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
        max_retries: Maximum number of retry attempts
        
    Returns:
        pd.DataFrame: DataFrame with OHLCV data or empty DataFrame on failure
    """
    ticker_clean = ticker.strip().upper()
    if not ticker_clean.endswith((".NS", ".BO")) and len(ticker_clean) > 1 and "^" not in ticker_clean:
        ticker_clean += ".NS"
    
    # Try multiple data sources with retries
    loaders = [_load_with_yahooquery, _load_with_yfinance_direct, _load_with_alpha_vantage]
    
    for attempt in range(max_retries):
        for loader in loaders:
            try:
                df = loader(ticker_clean, period, interval)
                if not df.empty:
                    logger.info(f"Successfully loaded data for {ticker_clean} using {loader.__name__}")
                    return df
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} with {loader.__name__} failed: {str(e)[:200]}")
                continue
        
        if attempt < max_retries - 1:
            wait_time = (attempt + 1) * 2  # Exponential backoff
            logger.info(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
    
    logger.error(f"All data loading attempts failed for {ticker_clean}")
    return pd.DataFrame()

def _load_with_yahooquery(ticker: str, period: str, interval: str) -> pd.DataFrame:
    """Load data using yahooquery (most reliable method)."""
    try:
        t = Ticker(ticker, asynchronous=True, max_workers=4)
        df = t.history(period=period, interval=interval)
        
        if df.empty:
            return pd.DataFrame()
            
        if isinstance(df.index, pd.MultiIndex):
            df = df.droplevel(0) if df.index.nlevels > 1 else df.reset_index(level=0, drop=True)
            
        column_map = {
            'open': 'Open', 'high': 'High', 'low': 'Low',
            'close': 'Close', 'adjclose': 'Adj Close', 'volume': 'Volume'
        }
        df = df.rename(columns={k: v for k, v in column_map.items() if k in df.columns})
        
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        df = df[[c for c in required_cols if c in df.columns]]
        df = df.dropna(subset=['Open', 'High', 'Low', 'Close'])
        
        return df
    except Exception as e:
        logger.warning(f"YahooQuery load failed: {str(e)[:200]}")
        raise

def _load_with_yfinance_direct(ticker: str, period: str, interval: str) -> pd.DataFrame:
    """Fallback to yfinance with custom session handling."""
    try:
        import yfinance as yf
        
        # Create a new session with custom headers
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Try to get crumb first
        try:
            crumb_url = 'https://query1.finance.yahoo.com/v1/test/getcrumb'
            session.get('https://finance.yahoo.com', timeout=10)
            crumb = session.get(crumb_url, timeout=10).text
            if not crumb:
                raise ValueError("Empty crumb received")
        except Exception:
            # If crumb fetch fails, proceed without it (some endpoints work without it)
            crumb = None
        
        # Download data with retries
        ticker_obj = yf.Ticker(ticker, session=session)
        df = ticker_obj.history(period=period, interval=interval, auto_adjust=False, progress=False)
        
        if df.empty:
            return pd.DataFrame()
            
        # Ensure proper column names and index
        df = df.rename(columns={
            'Open': 'Open', 'High': 'High', 'Low': 'Low',
            'Close': 'Close', 'Adj Close': 'Adj Close', 'Volume': 'Volume'
        })
        
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        df = df[[c for c in required_cols if c in df.columns]]
        df = df.dropna(subset=['Open', 'High', 'Low', 'Close'])
        
        return df
    except Exception as e:
        logger.warning(f"yfinance direct load failed: {str(e)[:200]}")
        raise

def _load_with_alpha_vantage(ticker: str, period: str, interval: str) -> pd.DataFrame:
    """Last resort: Try Alpha Vantage if API key is available."""
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    if not api_key:
        raise ValueError("Alpha Vantage API key not found")
    
    try:
        # Map period to Alpha Vantage's output size
        output_size = 'full' if any(x in period for x in ['10y', 'max', 'ytd', '5y', '2y']) else 'compact'
        
        # Map interval to Alpha Vantage's time frame
        if 'm' in interval or 'h' in interval:
            function = 'TIME_SERIES_INTRADAY'
            interval_av = interval.replace('m', 'min').replace('h', 'min')
            if 'min' in interval_av and int(interval_av.replace('min', '')) < 5:
                interval_av = '5min'  # Minimum interval is 5 minutes
        else:
            function = 'TIME_SERIES_DAILY_ADJUSTED'
            interval_av = ''
        
        # Build URL
        base_url = 'https://www.alphavantage.co/query'
        params = {
            'function': function,
            'symbol': ticker.replace('.NS', '').replace('.BO', ''),
            'apikey': api_key,
            'outputsize': output_size,
            'datatype': 'json'
        }
        if interval_av:
            params['interval'] = interval_av
        
        # Make request
        response = requests.get(base_url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Parse response
        if function == 'TIME_SERIES_DAILY_ADJUSTED':
            time_series = data.get('Time Series (Daily)', {})
            df = pd.DataFrame.from_dict(time_series, orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.rename(columns={
                '1. open': 'Open',
                '2. high': 'High',
                '3. low': 'Low',
                '4. close': 'Close',
                '5. adjusted close': 'Adj Close',
                '6. volume': 'Volume'
            })
        else:  # INTRADAY
            time_series = data.get(f'Time Series ({interval_av})', {})
            df = pd.DataFrame.from_dict(time_series, orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.rename(columns={
                '1. open': 'Open',
                '2. high': 'High',
                '3. low': 'Low',
                '4. close': 'Close',
                '5. volume': 'Volume'
            })
        
        # Convert string values to float
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Sort by date (oldest first)
        df = df.sort_index()
        
        # Ensure we have required columns
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        df = df[[c for c in required_cols if c in df.columns]]
        df = df.dropna(subset=['Open', 'High', 'Low', 'Close'])
        
        return df
    except Exception as e:
        logger.warning(f"Alpha Vantage load failed: {str(e)[:200]}")
        raise

# Alias for backward compatibility
load_data = safe_load_data

def load_intraday_alpha_vantage(ticker, interval="5min", outputsize="full", api_key=None):
    """
    Fetches intraday data from Alpha Vantage for high-frequency trading modes.
    """
    if not api_key or TimeSeries is None:
        return pd.DataFrame()

    try:
        ts = TimeSeries(key=api_key, output_format='pandas')
        # Pylance sometimes misinterprets the return type of get_intraday, explicitly unpack to avoid issues.
        data, _, meta_data = ts.get_intraday(symbol=ticker, interval=interval, outputsize=outputsize)

        if data.empty:
            return pd.DataFrame()

        # Rename columns to match expected format
        column_map = {
            '1. open': 'Open',
            '2. high': 'High',
            '3. low': 'Low',
            '4. close': 'Close',
            '5. volume': 'Volume'
        }
        data = data.rename(columns=column_map)

        # Ensure datetime index
        data.index = pd.to_datetime(data.index)
        data = data.sort_index()

        # Add Adj Close as Close for compatibility
        data['Adj Close'] = data['Close']

        return data
    except Exception as e:
        logger.error(f"Alpha Vantage intraday failed for {ticker}: {e}")
        return pd.DataFrame()

def safe_load_data(ticker, preferred_period):
    """
    Tries multiple periods in descending order until data is found.
    Returns (data, used_period)
    """
    for p in [preferred_period, "2y", "1y", "6mo", "3mo"]:
        df = load_data(ticker, period=p)

        if df is not None and not df.empty:
            return df, p

    return None, None


@lru_cache(maxsize=1)
def get_nifty_data():
    try:
        t = Ticker("^NSEI")
        df = t.history(period="5y")
        if df.empty: return pd.Series(dtype=float)
        if isinstance(df.index, pd.MultiIndex):
            df = df.reset_index(level=0, drop=True)
        return df['close']
    except Exception:
        return pd.Series(dtype=float)

def detect_regime(df):
    """Institutional Regime Detection using GMM on Volatility and Returns."""
    regime_series = get_regime_series(df)
    return regime_series.iloc[-1]

def get_regime_series(df):
    """Generates a series of regime classifications for the entire dataframe."""
    if 'Return' not in df.columns or 'Volatility' not in df.columns:
        return pd.Series(index=df.index, data="Unknown")
        
    data = df[['Return', 'Volatility']].dropna()
    if len(data) < 100: return pd.Series(index=df.index, data="Unknown")
    
    gmm = GaussianMixture(n_components=3, random_state=42)
    regimes = gmm.fit_predict(data)
    
    means = gmm.means_
    quiet_idx = np.argmin(means[:, 1])
    volatile_idx = np.argmax(means[:, 1])
    
    def map_regime(idx):
        if idx == quiet_idx: return "Quiet"
        if idx == volatile_idx: return "Volatile"
        return "Neutral"
        
    regime_series = pd.Series([map_regime(i) for i in regimes], index=data.index)
    return regime_series.reindex(df.index, fill_value="Unknown")

def calculate_hurst(ts: pd.Series) -> float:
    """Calculates the Hurst Exponent to detect trend persistence (>0.5) or mean reversion (<0.5)."""
    try:
        if len(ts) < 100: return 0.5
        lags = range(2, 20)
        tau = [np.std(np.subtract(ts.iloc[lag:], ts.iloc[:-lag])) for lag in lags]
        poly = np.polyfit(np.log(lags), np.log(tau), 1)
        return poly[0]
    except:
        return 0.5

def calculate_entropy(ts, bins=10):
    """Calculates Shannon Entropy to measure market disorder/randomness."""
    try:
        if len(ts) < 20: return 0.0
        counts = np.histogram(ts, bins=bins)[0]
        probs = counts / np.sum(counts)
        probs = probs[probs > 0]
        return -np.sum(probs * np.log2(probs))
    except:
        return 0.0

def calculate_performance_metrics(returns, regimes=None, slippage_bps=5.0):
    """Institutional Standard: Calculates Sharpe, Sortino, Max Drawdown, CVaR, and TCA-adjusted returns."""
    if len(returns) < 5: return {"sharpe": 0.0, "sortino": 0.0, "max_drawdown": 0.0, "cvar": 0.0, "tca_adj_return": 0.0}, {}, {} # Return empty dicts for attribution and correlations
    
    # Apply Slippage/TCA (Transaction Cost Analysis)
    tca_cost = (slippage_bps / 10000.0)
    adj_returns = returns.copy()
    # Apply cost only to non-zero return days (active trades)
    adj_returns.loc[adj_returns != 0] -= tca_cost
    
    # Annualized Sharpe (assuming daily data)
    sharpe = np.sqrt(252) * adj_returns.mean() / adj_returns.std() if adj_returns.std() != 0 else 0
    
    # Annualized Sortino
    downside_deviation = np.sqrt(np.mean(np.minimum(0, adj_returns)**2))
    sortino = np.sqrt(252) * adj_returns.mean() / downside_deviation if downside_deviation != 0 else 0
    
    # Max Drawdown
    cum_returns = (1 + adj_returns).cumprod()
    peak = cum_returns.cummax()
    drawdown = (cum_returns - peak) / peak
    
    # CVaR (95% confidence) - Expected loss in the worst 5% of cases
    var_95 = np.percentile(adj_returns, 5)
    cvar_95 = adj_returns[adj_returns <= var_95].mean() if len(adj_returns[adj_returns <= var_95]) > 0 else 0.0

    core_metrics = { # Renamed to core_metrics to distinguish
        "sharpe": float(sharpe), 
        "sortino": float(sortino), 
        "max_drawdown": float(drawdown.min()),
        "cvar": float(cvar_95),
        "tca_adj_return": float(adj_returns.sum())
    }

    regime_attribution = {}
    if regimes is not None:
        attribution = {}
        for r in regimes.unique():
            if r == "Unknown": continue
            r_mask = (regimes == r)
            r_returns = adj_returns[r_mask]
            if len(r_returns) > 5:
                attribution[r] = {
                    "sharpe": float(np.sqrt(252) * r_returns.mean() / r_returns.std()) if r_returns.std() != 0 else 0,
                    "trades": int(len(r_returns[r_returns != 0]))
                }
        regime_attribution = attribution
    
    correlations = {} # Placeholder for correlations, not calculated here
    
    return core_metrics, regime_attribution, correlations

def calculate_portfolio_allocation(ticker_results: list) -> list:
    """
    Quantum-Inspired Portfolio Optimization (QIPO) with enhanced error handling.
    Maximizes Sharpe ratio with quantum-inspired constraints for diversification.
    
    Args:
        ticker_results: List of dicts with 'ticker', 'final_conf_label', 
                      'volatility', 'final_confidence' keys
                      
    Returns:
        List of dicts with 'ticker' and 'weight' for each allocation
    """
    if not ticker_results:
        logger.warning("No ticker results provided for portfolio allocation")
        return []

    try:
        # Input validation
        if not all(isinstance(t, dict) for t in ticker_results):
            raise ValueError("All ticker results must be dictionaries")
            
        required_keys = {'ticker', 'final_conf_label', 'volatility', 'final_confidence'}
        if not all(required_keys.issubset(t.keys()) for t in ticker_results):
            missing = [k for t in ticker_results 
                     for k in required_keys if k not in t]
            raise ValueError(f"Missing required keys in ticker results: {set(missing)}")

        # Filter for actionable signals
        active_set = [t for t in ticker_results 
                     if str(t.get('final_conf_label', '')).lower() == 'buy']
        
        if not active_set:
            logger.info("No 'Buy' signals found in ticker results")
            return []

        # Extract data with validation
        try:
            vols = np.array([float(t.get('volatility', 0.02)) for t in active_set])
            confidences = np.array([float(t.get('final_confidence', 0.5)) 
                                  for t in active_set])
        except (TypeError, ValueError) as e:
            logger.error(f"Error converting data types: {e}")
            return []

        # Input validation
        if np.any(vols < 0) or np.any(confidences < 0) or np.any(confidences > 1):
            logger.warning("Invalid values in volatility or confidence metrics")
            return []

        # Expected returns proportional to confidences
        expected_returns = confidences
        cov_matrix = np.diag(np.maximum(vols, 1e-6) ** 2)  # Avoid zero volatility
        n = len(active_set)

        def negative_sharpe(weights):
            try:
                portfolio_return = np.dot(weights, expected_returns)
                portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
                return -portfolio_return / (portfolio_vol + 1e-6)  # Avoid division by zero
            except Exception as e:
                logger.error(f"Error in Sharpe ratio calculation: {e}")
                return 0

        # Optimization constraints and bounds
        constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]
        bounds = [(0, 0.5) for _ in range(n)]  # No asset > 50%
        initial_weights = np.ones(n) / n  # Equal weights as initial guess

        # Run optimization
        try:
            result = sco.minimize(
                negative_sharpe,
                initial_weights,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints,
                options={'maxiter': 1000, 'ftol': 1e-6}
            )

            if not result.success:
                logger.warning(f"Optimization failed: {result.message}")
                return []

            # Process results
            final_weights = result.x
            
            # Apply quantum-inspired constraints
            final_weights = np.clip(final_weights, 0, 0.4)  # Max 40% per asset
            final_weights = final_weights / np.sum(final_weights)  # Renormalize
            
            # Prepare results with validation
            results = []
            for i, ticker_data in enumerate(active_set):
                weight = float(final_weights[i])
                if weight > 0.01:  # Only include allocations > 1%
                    results.append({
                        'ticker': str(ticker_data['ticker']),
                        'weight': round(weight, 4),  # Round to 4 decimal places
                        'confidence': float(confidences[i]),
                        'volatility': float(vols[i])
                    })
            
            # Sort by weight (descending)
            results.sort(key=lambda x: x['weight'], reverse=True)
            
            # Final validation and normalization
            if results:
                total_weight = sum(a['weight'] for a in results)
                if abs(total_weight - 1.0) > 1e-6:  # If not already normalized
                    for a in results:
                        a['weight'] = round(a['weight'] / total_weight, 4)
                
                logger.info(f"Successfully allocated portfolio across {len(results)} assets")
                return results
            
            logger.warning("No valid allocations found after processing")
            return []
            
        except Exception as e:
            logger.error(f"Optimization error: {str(e)}")
            return []
            
    except Exception as e:
        logger.error(f"Error in portfolio allocation: {str(e)}")
        return []
    
    return []  # Fallback return

def bayesian_signal_fusion(probs, weights, prior=0.5, **context):
    """
    Institutional Layer 5: Combines model probabilities using Bayesian updating with symbolic rules.
    Treats each model as independent evidence to update the prior belief.
    Incorporates symbolic rules for MNSAI (Multi-Modal Neural Symbolic AI) based on context.
    """
    # Apply symbolic rules based on context
    regime = context.get('regime', 'Neutral')
    entropy = context.get('entropy', 0.0)
    beta = context.get('beta', 1.0)

    # Rule 1: Adjust weights based on regime
    if regime == "Volatile":
        # Increase LSTM weight by 20% in volatile regimes (price action matters more)
        weights[1] *= 1.2
    elif regime == "Quiet":
        # Increase RF weight by 20% in quiet regimes (technicals are more reliable)
        weights[0] *= 1.2

    # Rule 2: Adjust prior based on entropy (market disorder)
    if entropy > 0.85:
        # High entropy indicates chaotic market, reduce prior to be more conservative
        prior = 0.4

    # Rule 3: Adjust RF weight if high beta and RF signals buy (reduce over-reliance on correlated signals)
    if beta > 1.2 and probs[0] > 0.5:
        # High beta means high market correlation, reduce RF weight by 10%
        weights[0] *= 0.9

    # Normalize weights to sum to 1
    total_weight = sum(weights)
    if total_weight > 0:
        weights = [w / total_weight for w in weights]

    def prob_to_odds(p):
        p = np.clip(p, 0.01, 0.99)
        return p / (1 - p)

    combined_odds = prob_to_odds(prior)
    for p, w in zip(probs, weights):
        # Weight the influence of each model's evidence (Log-linear pooling)
        combined_odds *= (prob_to_odds(p) ** w)

    return combined_odds / (1 + combined_odds)

def calculate_correlation_matrix(base_ticker, comparison_tickers=["^NSEI", "^GSPC", "RELIANCE.NS", "TCS.NS"], period="1y"):
    """
    Institutional Data Layer: Generates a Correlation Regime Matrix.
    Ensures the system is aware of how the asset moves relative to major drivers.
    """
    try:
        data_map = {base_ticker: load_data(base_ticker, period=period)['Close'].pct_change()}
        for t in comparison_tickers:
            if t != base_ticker:
                data_map[t] = load_data(t, period=period)['Close'].pct_change()
        
        df_corr = pd.DataFrame(data_map).dropna()
        return df_corr.corr()[base_ticker].to_dict()
    except Exception:
        return {}

def apply_sentiment_decay(sentiment_df, half_life_days=3):
    """
    Alternative Data Layer: Models the 'Half-Life' of news impact.
    News from 3 days ago should have 50% of the weight of today's news.
    """
    if sentiment_df.empty: return sentiment_df
    
    sentiment_df = sentiment_df.sort_index()
    # Apply exponential decay: weight = 0.5 ^ (days_passed / half_life)
    days_passed = (sentiment_df.index[-1] - sentiment_df.index).days
    decay_weights = 0.5 ** (days_passed / half_life_days)
    sentiment_df['decayed_sentiment'] = sentiment_df['sentiment'] * decay_weights
    return sentiment_df

def estimate_implementation_shortfall(volatility, volume_participation=0.02):
    """
    Institutional Layer 8: Estimates market impact (slippage) using a square-root model.
    Impact = Volatility * sqrt(Participation_Rate)
    """
    # Participation rate of 2% of daily volume is a standard institutional benchmark
    return volatility * np.sqrt(volume_participation)

def run_monte_carlo_stress_test(returns, n_sims=1000, horizon=21):
    """Simulates 1000 possible future paths to estimate tail risk and probability of loss."""
    if len(returns) < 10: return {"prob_loss": 0.5, "p5_stress_outcome": 0.0}
    # Convert pandas Series to numpy array to avoid Pylance indexing issues with np.random.choice
    final_outcomes = []
    for _ in range(n_sims):
        sampled = np.random.choice(returns.values, size=horizon, replace=True)
        final_outcomes.append(np.prod(1 + sampled))
    
    final_outcomes = np.array(final_outcomes)
    return {
        "prob_loss": float(np.mean(final_outcomes < 1.0)),
        "p5_stress_outcome": float(np.percentile(final_outcomes, 5) - 1.0)
    }

def neutralize_features(df, exposure_cols=['Beta']):
    """Institutional Feature Neutralization to strip market Beta exposure."""
    if not any(col in df.columns for col in exposure_cols): return df
    
    cols_to_neutralize = [c for c in df.columns if c not in exposure_cols and c != 'Target']
    model = LinearRegression()
    
    # Work on a copy to avoid SettingWithCopyWarning
    temp_df = df.copy().fillna(0)
    exposure = temp_df[exposure_cols].values
    
    for col in cols_to_neutralize:
        y = temp_df[col].values
        model.fit(exposure, y) # Regress against Beta
        df[col] = df[col] - model.predict(exposure)
    return df

def calculate_feature_ic(df, feature_cols, target_col='Target', window=60):
    """
    Calculates Rolling Information Coefficient (IC) to monitor feature decay.
    IC is the correlation between a feature and the forward-looking target.
    """
    ic_results = {}
    if target_col not in df.columns:
        return {}
    for col in feature_cols:
        if col == target_col or col == 'Beta' or col not in df.columns: continue
        # Calculate rolling correlation between feature and target
        rolling_corr = df[col].rolling(window=window).corr(df[target_col])
        ic_results[col] = float(rolling_corr.iloc[-1]) if not np.isnan(rolling_corr.iloc[-1]) else 0.0
    return ic_results

def autocorr_lag1(x: pd.Series) -> float:
    return x.autocorr(lag=1)

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    if 'Close' not in df.columns or df.empty: return df
    df = df.copy()
    if 'Volume' in df.columns: df['Volume'] = df['Volume'].fillna(0)
    df = df.ffill() # REMOVED bfill to prevent future data leakage

    # --- WAVELET TRANSFORM (Noise Reduction) ---
    try:
        coeffs = pywt.wavedec(df['Close'], 'db4', level=4)
        # Pad the approximation coefficients to match the original length
        cA4 = np.pad(coeffs[0], (len(df) - len(coeffs[0]), 0), 'edge')
        df['Wavelet_Trend'] = cA4
    except Exception: # Fallback if wavelet fails (e.g., not enough data)
        df['Wavelet_Trend'] = df['Close'] # Fallback if wavelet fails

    # --- TARGET ENGINEERING: STATIONARY LOG-RETURNS ---
    # Log-returns are additive and handle non-stationarity better than raw price.
    df['Log_Return'] = np.log(df['Close'] / df['Close'].shift(1)).fillna(0)
    df['Volatility'] = df['Log_Return'].rolling(window=20).std()

    # --- STATISTICAL FEATURES (REGIME AWARENESS) ---
    df['Hurst'] = df['Close'].rolling(window=100).apply(calculate_hurst, raw=True)  # type: ignore
    df['Entropy'] = df['Log_Return'].rolling(window=20).apply(calculate_entropy, raw=True).astype(float)  # type: ignore # Ensure float type
    df['Autocorr_1'] = df['Log_Return'].rolling(window=20).apply(autocorr_lag1, raw=False)  # type: ignore

    # --- MICROSTRUCTURE PROXIES ---
    df['Vol_Delta'] = (df['Close'] - df['Open']) / (df['High'] - df['Low']).replace(0, 1e-9) * df['Volume']
    df['Liquidity_Imbalance'] = df['Vol_Delta'].rolling(window=20).mean() / df['Volume'].rolling(window=20).mean().replace(0, 1e-9)
    # Added: Order Flow Imbalance (OFI) proxy to capture liquidity pressure
    df['OFI'] = df['Vol_Delta'].diff().rolling(window=5).mean()

    # RSI
    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(span=14, adjust=False, min_periods=14).mean()
    avg_loss = loss.ewm(span=14, adjust=False, min_periods=14).mean()
    rs = avg_gain / avg_loss.replace(0, 1e-9) 
    df['RSI'] = 100 - (100 / (1 + rs))
    df['RSI_Slope'] = df['RSI'].diff(3) # Added: Momentum of RSI

    # MACD
    df['MACD'] = df['Close'].ewm(span=12, adjust=False).mean() - df['Close'].ewm(span=26, adjust=False).mean()
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['Signal_Line'] # Added: MACD Histogram (Divergence)

    # SMAs/EMAs
    df['SMA20'] = df['Close'].rolling(20, min_periods=1).mean()
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['SMA50'] = df['Close'].rolling(50, min_periods=1).mean()
    df['Dist_SMA50'] = (df['Close'] - df['SMA50']) / df['SMA50']
    
    # Volatility & Context
    df['RVOL'] = df['Volume'] / df['Volume'].rolling(window=20).mean() # Relative Volume
    
    # Seasonality (The "Logical" Context)
    # Ensure index is DatetimeIndex
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index, errors='coerce')
    df['DayOfWeek'] = df.index.dayofweek
    df['Month'] = df.index.month
    # Added for Nano/Intraday patterns
    if hasattr(df.index, 'hour'): df['Hour'] = df.index.hour
    if hasattr(df.index, 'minute'): df['Minute'] = df.index.minute

    # On-Balance Volume (OBV)
    df['OBV'] = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()

    # Bollinger Bands
    df['Middle_BB'] = df['SMA20']
    df['Std_BB'] = df['Close'].rolling(window=20).std()
    df['Upper_BB'] = df['Middle_BB'] + 2 * df['Std_BB']
    df['Lower_BB'] = df['Middle_BB'] - 2 * df['Std_BB']
    df['BB_PctB'] = (df['Close'] - df['Lower_BB']) / (df['Upper_BB'] - df['Lower_BB']).replace(0, 1e-9)
    df['BB_Width'] = (df['Upper_BB'] - df['Lower_BB']) / df['Middle_BB']

    # Stochastic Oscillator
    low_14 = df['Low'].rolling(window=14).min()
    high_14 = df['High'].rolling(window=14).max()
    df['Stoch_K'] = 100 * ((df['Close'] - low_14) / (high_14 - low_14).replace(0, 1e-9))
    df['Stoch_D'] = df['Stoch_K'].rolling(window=3).mean()

    # CCI (Commodity Channel Index)
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    cci = (tp - tp.rolling(20).mean()) / (0.015 * tp.rolling(20).std())
    df['CCI'] = cci
    
    # Williams %R
    df['WilliamsR'] = -100 * ((high_14 - df['Close']) / (high_14 - low_14).replace(0, 1e-9))

    # TR (True Range) - must be calculated before ADX and ATR
    high_low = df['High'] - df['Low']
    high_close_prev = np.abs(df['High'] - df['Close'].shift(1))
    low_close_prev = np.abs(df['Low'] - df['Close'].shift(1))
    df['TR'] = pd.concat([high_low, high_close_prev, low_close_prev], axis=1).max(axis=1)  # type: ignore

    # ADX (Average Directional Index)
    df['UpMove'] = df['High'] - df['High'].shift(1)
    df['DownMove'] = df['Low'].shift(1) - df['Low']
    df['PlusDM'] = np.where((df['UpMove'] > df['DownMove']) & (df['UpMove'] > 0), df['UpMove'], 0)
    df['MinusDM'] = np.where((df['DownMove'] > df['UpMove']) & (df['DownMove'] > 0), df['DownMove'], 0)
    df['PlusDI'] = 100 * (df['PlusDM'].ewm(alpha=1/14, adjust=False).mean() / df['TR'].ewm(alpha=1/14, adjust=False).mean())
    df['MinusDI'] = 100 * (df['MinusDM'].ewm(alpha=1/14, adjust=False).mean() / df['TR'].ewm(alpha=1/14, adjust=False).mean())
    df['DX'] = 100 * (np.abs(df['PlusDI'] - df['MinusDI']) / (df['PlusDI'] + df['MinusDI']).replace(0, 1e-9))
    df['ADX'] = df['DX'].ewm(alpha=1/14, adjust=False).mean()

    # ATR
    df['ATR'] = df['TR'].ewm(span=14, adjust=False, min_periods=14).mean()
    
    # Rate of Change (Momentum)
    df['ROC'] = df['Close'].pct_change(periods=10) * 100

    # VWAP (Volume Weighted Average Price)
    cum_vol = df['Volume'].cumsum()
    cum_vol_price = (df['Volume'] * (df['High'] + df['Low'] + df['Close']) / 3).cumsum()
    df['VWAP'] = cum_vol_price / cum_vol.replace(0, 1)

    # --- HIGH DIMENSIONALITY UPGRADE ---
    # Extensive Lagging to capture temporal dependencies (Memory)
    lags = [1, 2, 3, 5, 10, 21]
    for lag in lags:
        df[f'Lag_Return_{lag}'] = df['Log_Return'].shift(lag)
        df[f'Lag_RSI_{lag}'] = df['RSI'].shift(lag)
        df[f'Lag_MACD_{lag}'] = df['MACD'].shift(lag)
        df[f'Lag_ATR_{lag}'] = df['ATR'].shift(lag)
        df[f'Lag_Vol_{lag}'] = df['Volume'].pct_change().shift(lag)
    
    # New Features for Accuracy
    df['EMA_Cross'] = df['EMA9'] - df['SMA20']
    df['Vol_Change'] = df['Volume'].pct_change().fillna(0)
    
    # 1. Garman-Klass Volatility (Uses OHLC for better precision than Std Dev)
    log_hl = np.log(df['High'] / df['Low'].replace(0, 1))
    log_co = np.log(df['Close'] / df['Open'].replace(0, 1))
    df['Garman_Klass_Vol'] = np.sqrt(0.5 * log_hl**2 - (2 * np.log(2) - 1) * log_co**2)
    df['VoV'] = df['Garman_Klass_Vol'].rolling(window=20).std()

    # 2. Choppiness Index (Detects Trending vs Ranging markets)
    df['Sum_TR'] = df['TR'].rolling(14).sum()
    df['Range_HL'] = df['High'].rolling(14).max() - df['Low'].rolling(14).min()
    df['Choppiness'] = 100 * np.log10(df['Sum_TR'] / df['Range_HL'].replace(0, 1)) / np.log10(14)
    
    # --- INSTITUTIONAL FLOW & MARKET CONTEXT ---
    # 3. Money Flow Index (MFI) - Crucial for large caps like Airtel
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    raw_money_flow = typical_price * df['Volume']
    
    positive_flow = np.where(typical_price > typical_price.shift(1), raw_money_flow, 0)
    negative_flow = np.where(typical_price < typical_price.shift(1), raw_money_flow, 0)
    
    mf_ratio = pd.Series(positive_flow, index=df.index).rolling(14).sum() / pd.Series(negative_flow, index=df.index).rolling(14).sum().replace(0, 1e-9)
    df['MFI'] = (100 - (100 / (1 + mf_ratio))).astype(float) # Ensure float type

    # 4. Vortex Indicator (Trend Reversal)
    tr14 = df['TR'].rolling(14).sum()
    vm_plus = np.abs(df['High'] - df['Low'].shift(1))
    vm_minus = np.abs(df['Low'] - df['High'].shift(1))
    df['VI_Plus'] = vm_plus.rolling(14).sum() / tr14.replace(0, 1e-9)
    df['VI_Minus'] = vm_minus.rolling(14).sum() / tr14.replace(0, 1e-9)

    # 5. Market Correlation (Beta & RS)
    try:
        nifty_series = get_nifty_data()
        if not nifty_series.empty:
            # Align Nifty data to stock dates
            nifty_aligned = nifty_series.reindex(df.index).ffill()
            
            # Relative Strength (Stock vs Market) - Shifted to prevent lookahead bias
            df['RS_Rating'] = (df['Close'] / nifty_aligned.replace(0, 1)).shift(1)
            
            # Beta (60-day rolling volatility relative to market) - Shifted to prevent lookahead bias
            cov = df['Close'].pct_change().rolling(60).cov(nifty_aligned.pct_change())
            var = nifty_aligned.pct_change().rolling(60).var()
            df['Beta'] = ((cov / var.replace(0, 1e-9)).fillna(1.0)).shift(1)
    except Exception as e:
        print(f"Warning: Failed to calculate Beta/RS: {e}")
        pass
    
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.ffill().bfill() # Fill forward and backward to handle NaNs
    df = df.dropna(subset=['Close']) # Only drop rows where Close is NaN
    return df

def wavelet_denoise(data, wavelet='db4', level=1):
    """
    Apply wavelet soft-thresholding to a 1D signal.
    This helps to remove high-frequency noise while preserving the underlying signal.
    """
    # Decompose to get the wavelet coefficients
    coeff = pywt.wavedec(data, wavelet, mode="per")
    
    # Calculate sigma for thresholding from the detail coefficients
    sigma = (1/0.6745) * np.median(np.abs(coeff[-level]))

    # Calculate the universal threshold
    uthresh = sigma * np.sqrt(2 * np.log(len(data)))

    # Apply soft thresholding to detail coefficients
    coeff[1:] = (pywt.threshold(i, value=uthresh, mode='soft') for i in coeff[1:])

    # Reconstruct the signal
    reconstructed_signal = pywt.waverec(coeff, wavelet, mode='per')

    # Pad if necessary to match original length
    if len(reconstructed_signal) < len(data):
        reconstructed_signal = np.pad(reconstructed_signal, (len(data) - len(reconstructed_signal), 0), 'edge')

    return reconstructed_signal[:len(data)]

def prepare_stock_data(df, ticker, train_split_pct=0.8, api_key=None):
    if df is None or df.empty or 'Close' not in df.columns: return np.array([]), [], pd.DataFrame(), None, np.array([])
    
    df_indicators = add_indicators(df)
    df = df.merge(df_indicators.drop(columns=df.columns, errors='ignore'), left_index=True, right_index=True, how='left')

    # --- ALPHA MINING ---
    if api_key:
        alpha_formula = generate_alpha_feature(ticker, df.columns, api_key)
        if alpha_formula:
            try:
                # Clean the formula to remove prefixes and ensure compatibility
                alpha_formula = alpha_formula.replace('np.', '').replace('math.', '').strip()
                # Explicitly pass numpy and math functions into the local_dict
                df['LLM_Alpha'] = df.eval(
                    alpha_formula,
                    local_dict={
                        'np': np,
                        'abs': np.abs,
                        'log': np.log,
                        'sqrt': np.sqrt,
                        'exp': np.exp,
                        'sin': np.sin,
                        'cos': np.cos,
                        'tan': np.tan,
                        'mean': np.mean,
                        'std': np.std,
                        'min': np.min,
                        'max': np.max
                    },
                    engine='python'
                )
                df['LLM_Alpha'] = df['LLM_Alpha'].replace([np.inf, -np.inf], np.nan).fillna(0)
            except Exception as e:
                logger.error(f"Failed to evaluate alpha formula: {e}")

    # --- WAVELET SOFT-THRESHOLD DENOISING ---
    # Denoise key features to strip out high-frequency noise for the TFT model
    top_features_to_denoise = ['Log_Return', 'RSI', 'WilliamsR', 'CCI', 'ADX']
    for feature in top_features_to_denoise:
        if feature in df.columns:
            if len(df[feature].dropna()) > 20: # Ensure enough data points
                df[feature] = wavelet_denoise(df[feature].values)

    # --- MULTI-MODAL: ADD NEWS EMBEDDINGS ---
    news_embeddings = get_news_embeddings(ticker)
    if news_embeddings is not None and not news_embeddings.empty:
        df = df.merge(news_embeddings, left_index=True, right_index=True, how='left')
        # Fill days with no news with 0
        embedding_cols = [c for c in df.columns if c.startswith('emb_')]
        df[embedding_cols] = df[embedding_cols].fillna(0)

    df = make_columns_unique(df)
    
    # Store original close prices for inverse transform later
    original_close_prices = df['Close'].values
    
    # Use Log_Return as the prediction target
    df = df.rename(columns={'Log_Return': 'Target'})
    
    # Selecting the features for LSTM training
    # REMOVED LEAKY/REDUNDANT COLUMNS: VWAP (often leaks if not anchored), BB bands (derived from SMA/Std)
    cols_to_drop = ['Ticker', 'TR', 'Adj Close', 'Middle_BB', 'Std_BB', 'Upper_BB', 'Lower_BB', 'Signal_Line', 'UpMove', 'DownMove', 'PlusDM', 'MinusDM', 'PlusDI', 'MinusDI', 'DX', 'VWAP'] 
    feature_cols = [c for c in df.columns if c not in cols_to_drop and df[c].dtype in [np.float64, np.int64] and c != 'Close' and c != 'Target']
    
    # Ensure 'Target' is the first column for target extraction simplicity (target_col_idx=0) 
    feature_cols.insert(0, 'Target') 
    
    numeric_df = df[feature_cols].replace([np.inf, -np.inf], np.nan)
    numeric_df = numeric_df.fillna(0) # Fill NaNs with 0 to prevent dropping rows

    if len(numeric_df) < 5: # Lower threshold for shorter datasets
        return np.array([]), [], pd.DataFrame(), None, np.array([])

    # Align original prices with the feature dataframe
    aligned_original_prices = df.loc[numeric_df.index]['Close'].values

    # --- CRITICAL FIX: SCALER LEAKAGE ---
    # Fit scaler ONLY on training data
    split_idx = int(len(numeric_df) * train_split_pct)
    scaler = RobustScaler()
    
    # Fit on Train
    scaler.fit(numeric_df.iloc[:split_idx])
    
    # --- FEATURE NEUTRALIZATION (Idiosyncratic Alpha) ---
    numeric_df = neutralize_features(numeric_df)

    # Transform All (Train + Test)
    features = scaler.transform(numeric_df)
    
    return features, df.loc[numeric_df.index].index, numeric_df, scaler, aligned_original_prices

def prepare_data_sequences(data, time_steps, target_col_idx):
    if len(data) < time_steps + 1: return np.array([]), np.array([])
    
    # Vectorized sequence creation for speed
    # Create indices for the sliding window
    indices = np.arange(len(data) - time_steps)
    X = np.array([data[i:i + time_steps] for i in indices])
    y = data[time_steps:, target_col_idx]
    return X, y

def neg_log_likelihood(y_true, y_pred):
    return -y_pred.log_prob(y_true)

class GatedLinearUnit(tf.keras.layers.Layer):
    """Gated Linear Unit"""
    def __init__(self, units):
        super(GatedLinearUnit, self).__init__()
        self.linear = tf.keras.layers.Dense(units)
        self.sigmoid = tf.keras.layers.Dense(units, activation="sigmoid")

    def call(self, inputs):
        return self.linear(inputs) * self.sigmoid(inputs)

class GatedResidualNetwork(tf.keras.layers.Layer):
    """Gated Residual Network"""
    def __init__(self, units, dropout_rate):
        super(GatedResidualNetwork, self).__init__()
        self.units = units
        self.dropout_rate = dropout_rate
        self.dense1 = tf.keras.layers.Dense(self.units, activation="elu")
        self.dense2 = tf.keras.layers.Dense(self.units)
        self.glu = GatedLinearUnit(self.units)
        self.layer_norm = tf.keras.layers.LayerNormalization()
        self.dropout = tf.keras.layers.Dropout(self.dropout_rate)
        self.project = None

    def build(self, input_shape):
        if input_shape[-1] != self.units:
            self.project = tf.keras.layers.Dense(self.units)
        super(GatedResidualNetwork, self).build(input_shape)

    def call(self, inputs):
        x = self.dense1(inputs)
        x = self.dense2(x)
        x = self.dropout(x)
        shortcut = self.project(inputs) if self.project is not None else inputs
        x = self.layer_norm(x + shortcut)
        return self.glu(x)

class VariableSelectionNetwork(tf.keras.layers.Layer):
    """Variable Selection Network"""
    def __init__(self, num_features, hidden_units, dropout_rate):
        super(VariableSelectionNetwork, self).__init__()
        self.grn = GatedResidualNetwork(hidden_units, dropout_rate)
        self.softmax_dense = tf.keras.layers.Dense(num_features, activation="softmax")

    def call(self, inputs):
        # inputs shape: (batch_size, time_steps, num_features)
        # Flatten time and batch dimensions to process each feature vector
        # Shape becomes: (batch_size * time_steps, num_features)
        flattened_inputs = tf.reshape(inputs, [-1, tf.shape(inputs)[-1]])
        
        # GRN processes each of these flattened feature vectors
        grn_output = self.grn(flattened_inputs)
        
        # Get softmax weights
        sparse_weights = self.softmax_dense(grn_output)
        
        # Reshape weights back to (batch_size, time_steps, num_features)
        sparse_weights = tf.reshape(sparse_weights, tf.shape(inputs))
        
        # Multiply weights with original features
        weighted_features = inputs * sparse_weights
        
        return weighted_features

def create_tft_model(time_steps, n_features, lstm_units=128, lstm_units_2=128, dense_units=64, num_heads_1=8, num_heads_2=12, dropout_rate=0.2, learning_rate=0.001):
    """Creates a simplified Temporal Fusion Transformer model with adaptive attention heads."""
    
    inputs = Input(shape=(time_steps, n_features))
    
    # 1. Variable Selection
    vsn = VariableSelectionNetwork(n_features, dense_units, dropout_rate)
    selected_features = vsn(inputs)
    
    # 2. LSTM Encoder (deeper)
    # First Bi-LSTM Layer
    lstm_out = Bidirectional(LSTM(lstm_units, return_sequences=True))(selected_features)
    lstm_out = BatchNormalization()(lstm_out)
    lstm_out = Dropout(dropout_rate)(lstm_out)
    
    # Second Bi-LSTM Layer
    lstm_out = Bidirectional(LSTM(lstm_units_2, return_sequences=True))(lstm_out)
    lstm_out = BatchNormalization()(lstm_out)
    lstm_out = Dropout(dropout_rate)(lstm_out)

    # 3. Gated Residual Network after LSTM
    grn_lstm = GatedResidualNetwork(lstm_units_2 * 2, dropout_rate) # Output of Bi-LSTM is 2x units
    grn_lstm_out = grn_lstm(lstm_out)

    # 4. Multi-Head Self-Attention Layer 1
    attention_output_1 = MultiHeadAttention(num_heads=num_heads_1, key_dim=lstm_units_2 * 2)(query=grn_lstm_out, value=grn_lstm_out, key=grn_lstm_out)
    attention_output_1 = Dropout(dropout_rate)(attention_output_1)
    attention_output_1 = tf.keras.layers.LayerNormalization()(attention_output_1 + grn_lstm_out)

    # Multi-Head Self-Attention Layer 2
    attention_output_2 = MultiHeadAttention(num_heads=num_heads_2, key_dim=lstm_units_2 * 2)(query=attention_output_1, value=attention_output_1, key=attention_output_1)
    attention_output_2 = Dropout(dropout_rate)(attention_output_2)
    attention_output_2 = tf.keras.layers.LayerNormalization()(attention_output_2 + attention_output_1)
    
    # 5. Final Gated Residual Network
    final_grn = GatedResidualNetwork(lstm_units_2 * 2, dropout_rate)
    grn_output = final_grn(attention_output_2)
    
    # 6. Output Layer (take last time step)
    last_timestep_output = grn_output[:, -1, :]

    # Probabilistic output using TFP
    output_layer = tfpl.IndependentNormal(
        event_shape=1,
        convert_to_tensor_fn=tfp.distributions.Distribution.sample
    )(Dense(2)(last_timestep_output))  # 2 params: mean and std

    model = tf.keras.Model(inputs=inputs, outputs=output_layer)

    opt = tf.keras.optimizers.Adam(learning_rate=learning_rate)
    opt = tf.keras.mixed_precision.LossScaleOptimizer(opt)

    # Use negative log likelihood for probabilistic loss
    model.compile(optimizer=opt, loss=neg_log_likelihood)

    return model

# JIT compile the prediction step to reduce Python overhead in loops
@tf.function(reduce_retracing=True)
def fast_predict(model, input_tensor):
    predicted_distribution = model(input_tensor, training=False)
    return predicted_distribution.sample()

def predict_future(model, last_seq_scaled, scaler, n_future, target_col_idx, df_features, data):
    """Autoregressively predicts future prices by forecasting log returns with volatility."""
    cur_seq = last_seq_scaled.copy()
    future_scaled_log_returns = []

    df_extended = data.copy()

    for _ in range(n_future):
        input_tensor = tf.convert_to_tensor(cur_seq.reshape(1, *cur_seq.shape), dtype=tf.float32)

        # Use fast_predict to get sampled values
        pred_scaled_log_return = fast_predict(model, input_tensor).numpy()[0, 0]
        future_scaled_log_returns.append(pred_scaled_log_return)
        
        # --- Re-engineer features for the next time step ---
        # Inverse transform the prediction to get the true log return
        dummy_row = np.zeros((1, df_features.shape[1]))
        dummy_row[0, int(target_col_idx)] = pred_scaled_log_return
        pred_log_return = scaler.inverse_transform(dummy_row)[:, int(target_col_idx)]
        
        # Reconstruct the next price
        last_price = df_extended['Close'].iloc[-1]
        new_price = last_price * np.exp(pred_log_return)
        
        # Create a new row for the extended dataframe to calculate next-step indicators
        last_timestamp = df_extended.index[-1]
        new_timestamp = last_timestamp + pd.Timedelta(days=1) # Assuming daily data for future steps
        
        new_row_data = {
            'Open': last_price, 'High': new_price, 'Low': min(last_price, new_price),
            'Close': new_price, 'Volume': df_extended['Volume'].iloc[-20:].mean() # Use mean of recent volume
        }
        
        new_row_df = pd.DataFrame(new_row_data, index=[new_timestamp])
        df_extended = pd.concat([df_extended, new_row_df])
        
        # Recalculate all indicators
        df_extended_with_indicators = add_indicators(df_extended)
        
        # Scale the new features and update the input sequence for the next prediction
        required_cols = df_features.columns
        new_unscaled_features = df_extended_with_indicators.iloc[-1:].reindex(columns=required_cols, fill_value=0)
        new_scaled_features = scaler.transform(new_unscaled_features)
        
        cur_seq = np.roll(cur_seq, -1, axis=0)
        cur_seq[-1] = new_scaled_features
        
    # --- Reconstruct the final price path from the sequence of predicted log returns ---
    future_log_returns = inverse_transform_preds(np.array(future_scaled_log_returns), scaler, df_features.shape[1], target_col_idx)
    
    future_prices = []
    last_known_price = data['Close'].iloc[-1]
    for log_return in future_log_returns:
        next_price = last_known_price * np.exp(log_return)
        future_prices.append(next_price)
        last_known_price = next_price
    
    # Return future prices and empty arrays for uncertainty bands, which are no longer predicted
    return np.array(future_prices), np.array([])

def get_economic_calendar():
    """Simulates an institutional economic calendar. In production, this pulls from Bloomberg/Reuters."""
    # Return empty list to disable event blackout for testing
    return []

def check_event_blackout(ticker, calendar):
    """
    Checks for high-impact events (Earnings, Macro) that mandate a 'No Trade' zone.
    """
    now = datetime.datetime.now().date()
    for event in calendar:
        if event["date"] == now and event["impact"] == "High":
            return True
    return False 

def compute_prediction_error(y_true, y_pred):
    try:
        y_true = np.asarray(y_true)
        y_pred = np.asarray(y_pred)
        if len(y_true) == 0 or len(y_pred) == 0:
            return {"rmse": 0.0, "mae": 0.0, "mape": 0.0, "r2": 0.0} # Return 0.0 instead of None for empty inputs
        rmse = math.sqrt(mean_squared_error(y_true, y_pred))
        mae = mean_absolute_error(y_true, y_pred)
        mape = np.mean(np.abs((y_true - y_pred) / y_true.clip(min=1e-9))) * 100
        r2 = r2_score(y_true, y_pred)
        return {"rmse": float(rmse), "mae": float(mae), "mape": float(mape), "r2": float(r2)}
    except Exception: # Catch broader exceptions
        return {"rmse": 0.0, "mae": 0.0, "mape": 0.0, "r2": 0.0} # Return 0.0 for errors

def inverse_transform_preds(scaled_preds, scaler, n_features, target_col_idx):
    if scaled_preds.ndim == 1: scaled_preds = scaled_preds.reshape(-1, 1)
    dummy = np.zeros((len(scaled_preds), n_features))
    idx = int(target_col_idx) # Explicitly assign to a variable
    dummy[:, idx] = np.ravel(scaled_preds)
    return np.array(scaler.inverse_transform(dummy))[:, idx]

def calculate_max_drawdown(series):
    cummax = series.cummax()
    drawdown = (series - cummax) / cummax
    return drawdown.min()

class ThresholdWrapper(BaseEstimator):
    """Wraps a classifier to use a custom threshold on its probability predictions."""
    def __init__(self, model, threshold):
        self.model = model
        self.threshold = threshold
    def fit(self, X, y=None):
        # The wrapper doesn't need to be fitted, it uses the pre-fitted model
        return self
    def predict(self, X):
        # Get probabilities for the positive class and apply the custom threshold
        return (self.model.predict_proba(X)[:,1] >= self.threshold).astype(int)

def train_and_evaluate_rf(df, rf_params=None, gb_params=None):
    df = df.copy()
    if "Signal" not in df.columns or len(df) < 20: 
        return None, {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1_score": 0.0, "report": {}, "matrix": None, "optimal_threshold": 0.5}, [], pd.DataFrame()
    
    df['Signal'] = df['Signal'].astype(int).fillna(0)
    
    # Define features to drop: raw price data and redundant indicators
    X = df.drop(columns=[c for c in COLS_TO_DROP if c in df.columns], errors='ignore').select_dtypes(include=[np.number])
    X = X.replace([np.inf, -np.inf], np.nan)
    X = X.ffill().dropna()

    y = df["Signal"]
    feature_names = X.columns.tolist()
    
    # --- FEATURE PRUNING (IC-BASED) ---
    # Prune features with absolute IC < 0.02 to reduce noise before training
    ic_scores = calculate_feature_ic(df, feature_names, 'Signal', window=60)
    feature_names = [f for f in feature_names if abs(ic_scores.get(f, 0)) >= 0.02]
    X = X[feature_names]

    if len(X) < 20: 
        return None, {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1_score": 0.0, "report": {}, "matrix": None, "optimal_threshold": 0.5}, [], pd.DataFrame()

    split = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]

    # --- Defaults if no params provided ---
    if rf_params is None: rf_params = {'n_estimators': 500, 'max_depth': 25}

    # --- Intelligent Ensemble: Voting Classifier (RF + HGB + ET + Ada) ---
    # Combines the variance reduction of Random Forest/ExtraTrees with the bias reduction of Gradient Boosting.
    # This increases "intelligence" by capturing different types of patterns.
    
    class_weights = {0: 1.0, 1: 2.5}

    rf_clf = RandomForestClassifier(
        n_estimators=rf_params.get('n_estimators', 300), # Increased for accuracy
        max_depth=rf_params.get('max_depth', 25),
        min_samples_split=10, # Regularization: Require more samples to split
        min_samples_leaf=4,   # Regularization: Require more samples in leaf
        n_jobs=-1,
        random_state=42,
        class_weight=class_weights
    )
    
    et_clf = ExtraTreesClassifier(
        n_estimators=rf_params.get('n_estimators', 300),
        max_depth=rf_params.get('max_depth', 25),
        min_samples_split=10,
        min_samples_leaf=4,
        n_jobs=-1,
        random_state=42,
        class_weight=class_weights
    )
    
    hgb_clf = HistGradientBoostingClassifier(
        learning_rate=gb_params.get('learning_rate', 0.05) if gb_params else 0.05,
        max_iter=gb_params.get('n_estimators', 500) if gb_params else 500,
        max_depth=rf_params.get('max_depth', 15),
        l2_regularization=0.5,
        early_stopping=True,
        scoring='f1',
        random_state=42
    )
    
    base_model = VotingClassifier(
        estimators=[('rf', rf_clf), ('hgb', hgb_clf), ('et', et_clf)],
        voting='soft',
        n_jobs=-1
    )
    
    # --- PROBABILITY CALIBRATION (Platt Scaling) ---
    # Wrap the ensemble in a calibrated classifier to align probabilities.
    model = CalibratedClassifierCV(base_model, method='sigmoid', cv=3)
    
    # --- WALK-FORWARD VALIDATION (Institutional Standard) ---
    # Simulates periodic re-training to get robust performance metrics
    wfa_f1_scores = []
    n_splits = 3 # Reduced for API speed, but enough for a robust estimate
    step = len(X) // (n_splits + 1)
    
    for i in range(n_splits):
        train_end = step * (i + 1)
        test_end = train_end + step
        
        X_w_train, X_w_test = X.iloc[:train_end], X.iloc[train_end:test_end]
        y_w_train, y_w_test = y.iloc[:train_end], y.iloc[train_end:test_end]
        
        # Purging: Remove boundary samples to prevent leakage from rolling indicators
        if len(X_w_test) > 10:
            X_w_test = X_w_test.iloc[5:]
            y_w_test = y_w_test.iloc[5:]
            
        if len(X_w_test) < 5: continue
        
        fold_model = VotingClassifier(
            estimators=[('rf', rf_clf), ('hgb', hgb_clf), ('et', et_clf)],
            voting='soft', n_jobs=-1
        )
        fold_model.fit(X_w_train.values, y_w_train.values)
        y_w_proba = fold_model.predict_proba(X_w_test.values)[:, 1]
        y_w_pred = (y_w_proba >= 0.5).astype(int)
        wfa_f1_scores.append(f1_score(y_w_test, y_w_pred, average='weighted', zero_division=0))

    model.fit(X_train.values, y_train.values)

    if len(X_test) < 5: 
        return model, {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1_score": 0.0, "report": {}, "matrix": None, "optimal_threshold": 0.5, "wfa_f1": 0.0}, feature_names, pd.DataFrame()
        
    # --- Optimized Threshold Tuning (Vectorized) ---
    # Uses Precision-Recall Curve to find the optimal F1 threshold instantly (O(N) vs O(N*Steps))
    y_train_proba = model.predict_proba(X_train.values)[:, 1]
    
    precisions, recalls, thresholds = precision_recall_curve(y_train, y_train_proba)
    
    # Calculate F1 for all thresholds at once
    with np.errstate(divide='ignore', invalid='ignore'):
        f1_scores = 2 * (precisions * recalls) / (precisions + recalls)
    f1_scores = np.nan_to_num(f1_scores)
    
    best_idx = np.argmax(f1_scores)
    if best_idx < len(thresholds):
        best_thresh = thresholds[best_idx]
        best_score = f1_scores[best_idx]
    else:
        best_thresh = 0.5
        best_score = 0.0
            
    # Fallback: If model is still too defensive (F1 close to 0), force a percentile-based threshold
    if best_score < 0.1:
        optimal_threshold = float(np.percentile(y_train_proba, 85)) # Pick top 15% confident setups (Very selective)
    else:
        optimal_threshold = float(best_thresh)
    
    # Predict on test set using optimal threshold
    y_proba_test = model.predict_proba(X_test.values)[:, 1]
    y_pred = (y_proba_test >= optimal_threshold).astype(int)
    
    report = classification_report(y_test, y_pred, target_names=["Sell/Hold (0)", "Buy (1)"], output_dict=True, zero_division=0)
    matrix = confusion_matrix(y_test, y_pred)

    # Calculate Strategy Performance Metrics
    perf_metrics = {"sharpe": 0.0, "sortino": 0.0, "max_drawdown": 0.0, "cvar": 0.0} # Initialize with only core float metrics
    regime_attribution = {}
    correlations = {}
    stress_test = {"prob_loss": 0.5, "p5_stress_outcome": 0.0}

    if "Return" in df.columns:
        test_returns = df.loc[X_test.index, "Return"]
        strategy_returns = y_pred * test_returns
        
        regime_series = get_regime_series(df)
        test_regimes = regime_series.loc[X_test.index]
        
        core_perf_metrics, calculated_regime_attribution, calculated_correlations = calculate_performance_metrics(strategy_returns, test_regimes)
        
        perf_metrics = core_perf_metrics # Assign the core float metrics
        regime_attribution = calculated_regime_attribution
        correlations = calculate_correlation_matrix(df.index.name or "Asset") # Use the correct correlation calculation
        stress_test = run_monte_carlo_stress_test(strategy_returns.values)

    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, average="weighted", zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, average="weighted", zero_division=0)),
        "f1_score": float(f1_score(y_test, y_pred, average="weighted", zero_division=0)),
        "report": report,
        "matrix": matrix,
        "optimal_threshold": optimal_threshold,
        "wfa_f1": float(np.mean(wfa_f1_scores)) if wfa_f1_scores else 0.0,
        **perf_metrics, # Spread core float metrics
        "regime_attribution": regime_attribution, # Add attribution explicitly
        "correlations": correlations, # Add correlations explicitly
        "stress_test": stress_test
    }

    # --- FEATURE IMPORTANCE (OPTIMIZED) ---
    # Average feature importances from tree-based models in the ensemble
    # This is much faster than permutation_importance
    selected_features = feature_names  # Default to all features if importance fails
    feat_imp_df = pd.DataFrame()
    try:
        importances_rf = model.named_estimators_['rf'].feature_importances_
        importances_et = model.named_estimators_['et'].feature_importances_
        
        # HGB doesn't expose feature_importances_, so we average the other two
        avg_importances = (importances_rf + importances_et) / 2.0
        
        sorted_idx = avg_importances.argsort()[::-1]
        
        feat_imp_df = pd.DataFrame({
            "Feature": X_test.columns[sorted_idx],
            "Importance": avg_importances[sorted_idx]
        })

        # ================= FEATURE GATING (SMALL DATA SAFETY) =================
        # Remove weakest features to reduce overfitting on limited samples
        importance_threshold = np.percentile(
            feat_imp_df["Importance"], 25  # bottom 25% features
        )

        selected_features_imp = feat_imp_df.loc[
            feat_imp_df["Importance"] > importance_threshold,
            "Feature"
        ].tolist()

        # Safety fallback: never allow too few features
        if len(selected_features_imp) < 20:
            selected_features = feat_imp_df["Feature"].head(30).tolist()
        else:
            selected_features = selected_features_imp
            
    except Exception:
        pass # Fallback to using all features if importance calculation fails

    return model, metrics, selected_features, feat_imp_df


# --- SMART TRADE SETUP ENGINE ---
def calculate_smart_levels(df, current_price, signal_type):
    """
    Automates Target, Stop Loss, Support, Resistance, and Liquidity detection
    with dynamic ATR-based exits.
    """
    # 1. Pivot Points (Support/Resistance) - Using 14-period rolling window
    window = 14
    if not df.empty:
        df['Min'] = df['Low'].rolling(window=window, center=True).min()
        df['Max'] = df['High'].rolling(window=window, center=True).max()
        supports = df[df['Low'] == df['Min']]['Low'].unique()
        resistances = df[df['High'] == df['Max']]['High'].unique()
    else:
        supports = []
        resistances = []
        
    
    # Filter nearby levels (within reasonable range)
    supports = sorted([s for s in supports if s < current_price])[-3:] # 3 nearest below
    resistances = sorted([r for r in resistances if r > current_price])[:3] # 3 nearest above
    
    # 2. Liquidity Zones (Swing Highs/Lows)
    liquidity_msg = "Neutral"
    if not df.empty and len(df) > 5:
        if "Buy" in signal_type:
            # Check if price recently dipped below a support and reclaimed (Liquidity Sweep)
            recent_low = df['Low'].iloc[-5:].min()
            if recent_low < df['Low'].iloc[-1] and recent_low < current_price * 0.98:
                 liquidity_msg = "Liquidity Sweep (Bullish)"
        elif "Sell" in signal_type:
            recent_high = df['High'].iloc[-5:].max()
            if recent_high > df['High'].iloc[-1] and recent_high > current_price * 1.02:
                 liquidity_msg = "Liquidity Sweep (Bearish)"
             
    # 3. Dynamic ATR-Exit Logic
    atr = df['ATR'].iloc[-1] if 'ATR' in df.columns and not df.empty else current_price * 0.02
    
    setup = {
        "supports": [float(s) for s in supports],
        "resistances": [float(r) for r in resistances],
        "liquidity": liquidity_msg,
        "entry": float(current_price),
        "stop_loss": 0.0,
        "target": 0.0,
        "rr_ratio": "0:0"
    }
    
    # Determine calculation direction based on signal
    if "Buy" in signal_type:
        stop_loss = current_price - (1.5 * atr)
        target = current_price + (3.0 * atr)
        
        setup['stop_loss'] = float(stop_loss)
        setup['target'] = float(target)
        risk = current_price - stop_loss
        reward = target - current_price
        setup['rr_ratio'] = f"1:{(reward / risk):.2f}" if risk > 0 else "N/A"
        
    elif "Sell" in signal_type or "Avoid" in signal_type:
        stop_loss = current_price + (1.5 * atr)
        target = current_price - (3.0 * atr)
        
        setup['stop_loss'] = float(stop_loss)
        setup['target'] = float(target)
        risk = stop_loss - current_price
        reward = current_price - target
        setup['rr_ratio'] = f"1:{(reward / risk):.2f}" if risk > 0 else "N/A"
    else: # Neutral/Hold case - can still provide a hypothetical setup
        # The old logic for neutral seems fine, but let's make it consistent
        # with the new ATR logic to provide a what-if scenario.
        # Hypothetical long setup
        stop_loss = current_price - (1.5 * atr)
        target = current_price + (3.0 * atr)
        setup['stop_loss'] = float(stop_loss)
        setup['target'] = float(target)
        risk = current_price - stop_loss
        reward = target - current_price
        setup['rr_ratio'] = f"Hypothetical Long 1:{(reward / risk):.2f}" if risk > 0 else "N/A"

    return setup

# --- Sentiment Analysis Function ---
@lru_cache(maxsize=128)
def get_stock_news_sentiment(ticker: str, api_key=None, _ttl_hash=None):
    """
    Fetches news sentiment for a stock using multiple sources.
    Sources (in priority order):
    1. Alpha Vantage News API (requires ALPHA_VANTAGE_API_KEY)
    2. NewsAPI (requires NEWSAPI_API_KEY)
    3. Yahoo Finance via yahooquery
    """
    from nltk.sentiment.vader import SentimentIntensityAnalyzer

    sia = SentimentIntensityAnalyzer()
    sentiments = []
    news_items = []

    # Normalize ticker for consistent API calls
    normalized_ticker = normalize_ticker(ticker)
    clean_ticker = ticker.rstrip('.NS.BO')

    # ===== SOURCE 1: Alpha Vantage News =====
    alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    if alpha_vantage_key and NewsSentiment is not None:
        try:
            ns = NewsSentiment(key=alpha_vantage_key)
            data, _ = ns.get_news_sentiment(tickers=clean_ticker, limit=50)
            logger.info(f"✓ Alpha Vantage fetched {len(data)} news items for {ticker}")
            for item in data:
                title = item.get('title', '')
                url = item.get('url', '')
                time_published = item.get('time_published', '')
                if title:
                    score = sia.polarity_scores(title)["compound"]
                    dt = pd.to_datetime(time_published) if time_published else pd.Timestamp.now()
                    news_items.append({"title": title, "link": url, "sentiment": score, "date": dt, "source": "Alpha Vantage"})
        except Exception as e:
            logger.warning(f"⚠ Alpha Vantage News failed for {ticker}: {str(e)[:100]}")

    # ===== SOURCE 2: NewsAPI =====
    if not news_items or len(news_items) < 10:
        newsapi_key = os.getenv('NEWSAPI_API_KEY')
        if newsapi_key:
            try:
                import requests
                newsapi_url = "https://newsapi.org/v2/everything"
                
                params = {
                    "q": f'"{clean_ticker}" OR "{ticker}"',
                    "sortBy": "publishedAt",
                    "language": "en",
                    "pageSize": 50,
                    "apiKey": newsapi_key
                }
                
                response = requests.get(newsapi_url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    articles = data.get('articles', [])
                    logger.info(f"✓ NewsAPI fetched {len(articles)} news items")
                    
                    for article in articles:
                        title = article.get('title', '')
                        description = article.get('description', '') or ''
                        url = article.get('url', '')
                        pub_date = article.get('publishedAt', '')
                        
                        if title:
                            text = f"{title} {description}"
                            score = sia.polarity_scores(text)["compound"]
                            dt = pd.to_datetime(pub_date) if pub_date else pd.Timestamp.now()
                            news_items.append({"title": title, "link": url, "sentiment": score, "date": dt, "source": "NewsAPI"})
            except:
                pass

    # ===== Calculate Sentiment =====
    if not news_items:
        logger.warning(f"❌ No news found for {ticker} from AlphaVantage or NewsAPI. Using neutral sentiment (0.0)")
        return 0.0, []

    logger.info(f"✓ Total {len(news_items)} news items collected for {ticker} from multiple sources")

    # Apply Temporal Decay
    sent_df = pd.DataFrame(news_items).set_index('date')
    sent_df = apply_sentiment_decay(sent_df)
    avg_sentiment = float(sent_df['decayed_sentiment'].mean())

    return avg_sentiment, news_items

@lru_cache(maxsize=32)
def get_news_alpha_vantage(tickers=None, topics=None, limit=50, api_key=None, _ttl_hash=None):
    """
    Fetches news from Alpha Vantage for tickers or topics.
    Falls back to NewsAPI if Alpha Vantage unavailable.
    """
    if not api_key:
        api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    
    news_items = []
    sia = SentimentIntensityAnalyzer()
    
    # ===== Try Alpha Vantage First =====
    if api_key and NewsSentiment is not None:
        try:
            ns = NewsSentiment(key=api_key)
            data, _ = ns.get_news_sentiment(tickers=tickers, topics=topics, limit=limit)
            logger.info(f"✓ Alpha Vantage fetched {len(data)} news items")
            
            for item in data:
                title = item.get('title', '')
                url = item.get('url', '')
                time_published = item.get('time_published', '')
                if title:
                    score = sia.polarity_scores(title)["compound"]
                    dt = pd.to_datetime(time_published) if time_published else pd.Timestamp.now()
                    news_items.append({
                        "title": title, 
                        "link": url, 
                        "sentiment": score, 
                        "date": dt,
                        "source": "Alpha Vantage"
                    })
            return news_items
        except Exception as e:
            logger.warning(f"⚠ Alpha Vantage failed: {str(e)[:100]}")
    
    # ===== Fallback to NewsAPI =====
    newsapi_key = os.getenv('NEWSAPI_API_KEY')
    if newsapi_key:
        try:
            import requests
            search_query = ' OR '.join(tickers) if tickers else ' OR '.join(topics) if topics else 'stock market'
            
            newsapi_url = "https://newsapi.org/v2/everything"
            params = {
                "q": search_query,
                "sortBy": "publishedAt",
                "language": "en",
                "pageSize": limit,
                "apiKey": newsapi_key
            }
            response = requests.get(newsapi_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                logger.info(f"✓ NewsAPI fetched {len(articles)} news items")
                
                for article in articles:
                    title = article.get('title', '')
                    description = article.get('description', '') or ''
                    url = article.get('url', '')
                    pub_date = article.get('publishedAt', '')
                    
                    if title:
                        text = f"{title} {description}"
                        score = sia.polarity_scores(text)["compound"]
                        dt = pd.to_datetime(pub_date) if pub_date else pd.Timestamp.now()
                        news_items.append({
                            "title": title,
                            "link": url,
                            "sentiment": score,
                            "date": dt,
                            "source": "NewsAPI"
                        })
            else:
                logger.warning(f"⚠ NewsAPI returned status {response.status_code}")
        except Exception as e:
            logger.warning(f"⚠ NewsAPI failed: {str(e)[:100]}")
    
    return news_items


# --- Custom Prediction Function for Threshold Tuning ---
def predict_with_threshold(model, X_data, threshold=0.35):
    """Generates predictions based on a custom probability threshold."""
    if model is None:
        return np.array([])
    # Ensure prediction data is a NumPy array for scikit-learn compatibility
    if isinstance(X_data, pd.DataFrame):
        X_data = X_data.values 
        
    y_proba = model.predict_proba(X_data)[:, 1]
    return (y_proba >= threshold).astype(int)

def get_recommendation_label_from_proba(proba, threshold=0.35): # Optimized threshold for oversampled models
    if proba is None or len(proba) < 2: return "Uncertain", 0.0
    buy_prob = float(proba[1])
    sell_prob = float(proba[0])
    
    # Use the optimized threshold
    if buy_prob >= threshold: return "Buy", buy_prob
    elif sell_prob >= (1 - threshold): return "Sell/Hold", sell_prob
    else: return "Neutral/Hold", max(buy_prob, sell_prob)

# --- Fundamentals Fetching ---
def _safe_float_conversion(value):
    """Helper to safely convert a value to float, or return None if not possible."""
    if value is None:
        return None
    if isinstance(value, dict):
        value = value.get("raw")
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

# --- Fundamentals Fetching ---
def get_fundamentals(ticker: str) -> dict:
    ticker = normalize_ticker(ticker)

    try:
        t = Ticker(ticker)
        # Use t.key_stats and t.summary_detail directly
        key_stats = t.key_stats or {}
        summary = t.summary_detail or {}

        return {
            "Market Cap": _safe_float_conversion(summary.get("marketCap")),
            "Trailing P/E": _safe_float_conversion(key_stats.get("trailingPE")),
            "Forward P/E": _safe_float_conversion(key_stats.get("forwardPE")),
            "EPS": _safe_float_conversion(key_stats.get("trailingEps")),
            "Sector": summary.get("sector", None),
            "Industry": summary.get("industry", None),
            "52W High": _safe_float_conversion(summary.get("fiftyTwoWeekHigh")),
            "52W Low": _safe_float_conversion(summary.get("fiftyTwoWeekLow")),
        }
    except Exception:
        return {}

# --- ALPHA MINING (LLM-based Feature Engineering) ---
def generate_alpha_feature(ticker, existing_features, api_key):
    """Asks an LLM to create a new formulaic alpha feature."""
    if not api_key:
        return None

    # We don't want to send ALL features, just a curated list of potent ones.
    potent_features = [f for f in existing_features if f in [
        'RSI', 'MACD_Hist', 'Garman_Klass_Vol', 'MFI', 'CCI', 'RVOL', 
        'Choppiness', 'Beta', 'RS_Rating', 'Volatility'
    ]]
    if len(potent_features) < 5:
        return None # Not enough features to generate a meaningful formula

    try:
        system_prompt = "You are a quantitative analyst. Your task is to create a novel alpha factor formula from a given list of financial indicators. The formula must be a single line of Python code compatible with pandas' `df.eval()` method."
        
        user_prompt = f"""
        Given the following financial indicators for a stock: {', '.join(potent_features)}

        Create a new, non-obvious formula that combines at least two of these indicators to generate a new alpha factor.
        The formula should capture a specific market dynamic (e.g., momentum acceleration, volatility-weighted sentiment).

        **RULES:**
        1. The output MUST be a single line of Python code.
        2. Do NOT include "new_alpha =" or any variable assignment.
        3. Use only the provided indicator names and basic math operators (+, -, *, /, **, np.log, np.sqrt, np.abs).
        4. The formula should be mathematically sound and scaled reasonably (e.g., avoid division by zero).

        **Example output:** `(RSI - 50) * Garman_Klass_Vol`

        Generate a new formula for the ticker {ticker}:
        """
        
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.8,
            "max_tokens": 100
        }
        
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            formula = response.json()['choices'][0]['message']['content']
            # Clean up the response: remove markdown, newlines, etc.
            formula = re.sub(r'[`\n\r]', '', formula).strip()
            # Basic validation
            if any(op in formula for op in ['+', '-', '*', '/']):
                return formula
        return None
    except Exception:
        return None

# --- LLAMA API SIMULATION FOR REPORTING ---
def ai_report_and_tune(rf_metrics, feat_imp_df, target_threshold, ticker, fundamentals, chart_context, rf_signal, lstm_trend, final_conf, final_label, trade_setup, api_key=None):
    """Provides a dynamic, contextual report and critique of the model."""
    
    try:
        accuracy = float(rf_metrics.get('accuracy', 0.0))
    except (ValueError, TypeError):
        accuracy = 0.0

    try:
        precision = float(rf_metrics.get('precision', 0.0))
    except (ValueError, TypeError):
        precision = 0.0

    try:
        recall = float(rf_metrics.get('recall', 0.0))
    except (ValueError, TypeError):
        recall = 0.0

    try:
        f1 = float(rf_metrics.get('f1_score', 0.0))
    except (ValueError, TypeError):
        f1 = 0.0
    report = rf_metrics.get("report", "")
    matrix = rf_metrics.get("matrix", "N/A")
    
    top_features = feat_imp_df.head(5).to_dict(orient='records') if not feat_imp_df.empty else []
    
    # Attempt to extract Buy Precision and Recall
    try:
        buy_metrics = report.get("Buy (1)", {})
        buy_precision = float(buy_metrics.get("precision", 0.0))
        buy_recall = float(buy_metrics.get("recall", 0.0))
    except:
        buy_precision = 0.0
        buy_recall = 0.0

    # --- REAL LLAMA API CALL (GROQ) ---
    if api_key:
        try:
            system_prompt = "You are a senior quantitative financial analyst and AI expert. Your job is to generate a comprehensive financial theory report, including accounting analysis and technical chart explanation."
            
            user_prompt = f"""
            Generate a detailed Financial & AI Analysis Report for ticker **{ticker}**.
            
            **1. Accounting & Fundamental Analysis:**
            Use these values: {json.dumps(fundamentals, indent=2)}
            - Analyze the valuation (P/E, EPS) and financial health.
            - Comment on the sector/industry context if available.
            
            **Model Configuration:**
            - Target: Predict if next day's Close > current day's Close (Directional)
            - Buy Signal Threshold: {target_threshold} (Probability >= {target_threshold})
            
            **Performance Metrics (Test Set):**
            - Accuracy: {accuracy:.2f}
            - Overall Precision: {precision:.2f}
            - Overall Recall: {recall:.2f}
            - F1 Score: {f1:.2f}
            - Sharpe Ratio: {rf_metrics.get('sharpe', 0):.2f}
            - Max Drawdown: {rf_metrics.get('max_drawdown', 0):.2%}
            - CVaR (95%): {rf_metrics.get('cvar', 0):.2%}
            - Monte Carlo Prob. Loss (21d): {rf_metrics.get('stress_test', {}).get('prob_loss', 0):.1%}
            - Walk-Forward F1: {rf_metrics.get('wfa_f1', 0):.2f}
            - Regime Attribution: {json.dumps(rf_metrics.get('regime_attribution', {}), indent=2)}
            
            **Class-Specific Metrics (Important):**
            - Buy Signal Precision: {buy_precision:.2f} (Reliability of Buy signals)
            - Buy Signal Recall: {buy_recall:.2f} (Ability to catch profitable moves)
            
            **Top Predictive Features:**
            {json.dumps(top_features, indent=2)}

            **Feature Importance Details:**
            {json.dumps(feat_imp_df.to_dict(orient='records'), indent=2)}
            
            **Chart & Trend Context:**
            {chart_context}
            
            **Model Confluence:**
            - Ensemble Signal (RandomForest + HistGradientBoosting + ExtraTrees (Soft Voting)): {rf_signal}
            - LSTM Scenario Projection (Price Regression): {lstm_trend}
            - **Final System Decision:** {final_label} ({final_conf:.1%})

            **Automated AI Smart Trade Setup:**
            {json.dumps(trade_setup, indent=2)}
            
            **Report Sections Required:**
            1.  **Executive Summary:** A brief "Status" (Optimal/Needs Tuning/Poor) and main takeaway. Note: For stock market prediction, an accuracy above 55% is considered **Optimal**.
            1.  **Executive Summary:** A brief "Status" (Optimal/Needs Tuning/Poor) and main takeaway.
                *   **MANDATORY RULE:** If Accuracy is > 0.55 OR (Buy Precision > 0.50 and Buy Recall > 0.10), the Status MUST be **Optimal**.
                *   **Self-Correction:** If Buy Precision/Recall is 0.00 but Accuracy is high, do NOT report "Needs Tuning". Instead, report that the model is in **"Defensive Mode"**, correctly identifying that there are no high-probability buy setups in the current market conditions.
            2.  **Fundamental & Accounting Theory:** Explain the accounting values provided. Are they undervalued or overvalued based on theory?
            3.  **Technical & Chart Explanation:** Explain the recent price trend and the forecast provided in the context data. Relate it to the AI model's prediction.
            4.  **AI Model Critique:** Analyze the Precision/Recall trade-off and Feature Importance.
            5.  **Strategic Recommendation:** Concrete advice for the trader. **CRITICAL:** Treat the Ensemble and LSTM models as "Two Ways of Analysis". If they diverge, explain it as a nuance (e.g., "LSTM predicts a short-term pullback (Price Action), while Ensemble sees a bullish setup (Indicators)"). Do not call it an error; call it a multi-factor perspective.
            
            Format the output in clean Markdown with emojis. Use `##` for section headers. Keep it concise but professional.
            """
            
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1024
            }
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
            
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                print(f"Llama API returned error {response.status_code}. Falling back to internal logic.")
        except Exception as e:
            print(f"Failed to connect to Llama API: {e}. Falling back to internal logic.")
    
    # --- LLAMA CRITIQUE LOGIC ---
    if accuracy >= 0.55:
        llm_analysis = f"""
        ## 🧠 AI Model Analysis & Recommendation (Generated) 
        
        <p style='color:#4CAF50;'>**STATUS: OPTIMAL PERFORMANCE!** The model has achieved an overall accuracy of **{accuracy:.2f}** with reliable signal quality.</p>
        
        ### Performance Critique:
        The model shows excellent generalization. Buy Precision is strong, meaning Buy signals are highly reliable, and Recall is balanced, ensuring good capture of opportunities. The oversampling and parameter tuning have converged.
        
        ### Tuning Recommendation:
        **Recommendation:** Hold parameters stable. If testing on new data shows decay, slightly increase the `n_estimators` (to 600 or 700) to maintain robustness.
        """
    elif accuracy >= 0.50:
        llm_analysis = f"""
        ## 🧠 AI Model Analysis & Recommendation (Generated) 
        
        <p style='color:#FFD700;'>**STATUS: CONVERGENCE POINT.** The model has reached a competitive accuracy of **{accuracy:.2f}**, but the signal quality needs adjustment.</p>
        
        ### Performance Critique:
        * **Buy Precision ({buy_precision:.2f}):** This is the probability a "Buy" signal is correct. If this is **below 0.60**, your model is still prone to generating bad trades (False Positives).
        * **Buy Recall ({buy_recall:.2f}):** The ability to capture actual profitable moves. If this is 0.00, the model is currently in "Defensive Mode" and finding no setups meeting the strict criteria.
        
        ### Tuning Recommendation:
        Your model has high bias (too cautious). To correct this:
        1.  **If Buy Precision is LOW ($\\lt 0.50$):** Increase the training data period (e.g., from 1y to 2y).
        2.  **If Buy Recall is LOW ($\\lt 0.10$):** The system has already auto-adjusted the threshold to **{target_threshold:.2f}**. Consider increasing `future_days` to capture longer trends.
        """
    else:
         llm_analysis = """

        ## 🧠 AI Model Analysis & Recommendation (Generated) 
        
        <p style='color:red;'>**STATUS: POOR PERFORMANCE.** The model accuracy is below 60%. The current parameters and feature set are not generating stable patterns.</p>
        
        ### Immediate Action Required:
        1. **Increase Data Quality:** Ensure your chosen Ticker and Training Period cover a diverse range of market conditions (e.g., use a 2y period).
        2. **Retrain:** If the model continues to struggle, try slightly increasing `max_depth` to 20 or `n_estimators` to 700 to increase complexity.
        """
        
    return llm_analysis
# --- END LLAMA API SIMULATION ---

# --- REPORT QA FUNCTION ---
def ask_ai_about_report(report_text, question, api_key):
    """Allows QA on a specific report."""
    if not api_key:
        return "⚠️ API Key missing. Cannot perform QA."
    
    try:
        system_prompt = "You are a helpful financial assistant. You are answering questions about a specific stock analysis report provided by the user. Answer based ONLY on the report content provided."
        user_prompt = f"""
        **REPORT CONTENT:**
        {report_text}
        
        **USER QUESTION:**
        {question}
        
        Answer concisely and professionally.
        """
        
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.5,
            "max_tokens": 300
        }
        
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        return f"Error: {response.status_code}"
    except Exception as e:
        return f"Exception: {e}"

# --- PDF GENERATION ---
def create_pdf_report(text, ticker, fundamentals):
    if FPDF is None:
        return None # Explicitly return None if FPDF is not available
    
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 15)
            self.cell(0, 10, f'Financial Analysis Report: {ticker}', 0, 1, 'C')
            self.ln(5)
            
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    
    # Add Fundamentals Section
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Key Accounting & Fundamental Values:", 0, 1)
    pdf.set_font("Arial", size=10)
    
    fund_text = ", ".join([f"{k}: {v}" for k, v in fundamentals.items()])
    pdf.multi_cell(0, 8, fund_text)
    pdf.ln(5)
    
    # Add Main Report Text
    # Clean text for PDF (remove emojis and unsupported chars)
    clean_text = text.encode('latin-1', 'replace').decode('latin-1')
    # Remove markdown bolding ** for readability in plain text PDF
    clean_text = clean_text.replace('**', '').replace('##', '').replace('###', '')
    
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 6, clean_text)
    
    return pdf.output(dest='S').encode('latin-1')


# --- ULTRA-POWERFUL AI HYPERPARAMETER TUNING ---
def get_ai_hyperparameters(ticker, api_key, trading_mode="Swing"):
    """
    Aggressively enhanced AI-driven hyperparameter tuning for extreme power and efficiency.
    Uses dynamic volatility scaling, expanded ranges, and assertive prompts for maximum performance.
    """
    try:
        # Fetch fundamentals for sector/cap context
        fund = get_fundamentals(ticker)
        sector = fund.get("Sector", "Unknown")
        industry = fund.get("Industry", "Unknown")

        # Fetch context data for professional analysis
        df_context = load_data(ticker, period="1y")
        guidance_str = ""
        if not df_context.empty:
            returns = df_context['Close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252)
            trend = (df_context['Close'].iloc[-1] - df_context['Close'].iloc[0]) / df_context['Close'].iloc[0]

            # Liquidity / Volume Profile
            avg_volume = df_context['Volume'].mean()
            liquidity_status = "High" if avg_volume > 1000000 else "Medium" if avg_volume > 100000 else "Low"

            # AGGRESSIVE Dynamic Guidance Generation (Ultra-Powerful)
            guidance = []
            if volatility > 0.30:
                guidance.append("EXTREME VOLATILITY (>30%). FORCE SHORTEST future_days (3-7), MAX dropout_rate (0.4-0.5), DEEPEST trees (50+), LOWEST learning_rate (1e-5). PUSH FOR MAXIMUM STABILITY.")
            elif volatility < 0.15:
                guidance.append("ULTRA-STABLE (<15%). FORCE LONGEST future_days (40-60), MIN dropout_rate (0.05-0.1), HIGHEST learning_rate (0.1-0.2). EXPLOIT STABILITY FOR MAXIMUM ACCURACY.")

            if avg_volume < 200000:
                guidance.append("MICRO-LIQUIDITY. FORCE TINY batch_size (8-16), MINIMAL lstm_units (32-64). OPTIMIZE FOR SPEED OVER COMPLEXITY.")
            elif avg_volume > 2000000:
                guidance.append("MEGA-LIQUIDITY. FORCE MASSIVE batch_size (128-256), HUGE lstm_units (512-1024). SCALE FOR MAXIMUM POWER.")

            # Add Hurst Exponent for Trend Persistence
            hurst = calculate_hurst(df_context['Close'])
            if hurst > 0.6:
                guidance.append("STRONG TREND PERSISTENCE (Hurst >0.6). BOOST MOMENTUM FEATURES, INCREASE time_steps (120-180).")
            elif hurst < 0.4:
                guidance.append("HIGH MEAN REVERSION (Hurst <0.4). REDUCE time_steps (20-40), FOCUS ON SHORT-TERM OSCILLATORS.")

            guidance_str = "\n".join(guidance)

            context_str = (
                f"Sector: {sector} | Industry: {industry}\n"
                f"Annualized Volatility: {volatility:.2%} ({'Extreme' if volatility > 0.4 else 'High' if volatility > 0.3 else 'Low'})\n"
                f"1-Year Trend: {trend:.2%}\n"
                f"Liquidity: {liquidity_status} (Avg Vol: {int(avg_volume):,})\n"
                f"Hurst Exponent: {hurst:.2f} ({'Trending' if hurst > 0.5 else 'Reverting'})"
            )
        else:
            context_str = "Data unavailable for context."

        system_prompt = f"You are an ELITE Chief Data Scientist specializing in FINANCIAL TIME SERIES. You MUST deliver HYPER-OPTIMIZED, AGGRESSIVE hyperparameters for MAXIMUM PERFORMANCE. NO GENERIC DEFAULTS. PUSH BOUNDARIES FOR EXTREME EFFICIENCY AND POWER based on {trading_mode} trading mode."
        # Ultra-Powerful prompt with expanded ranges and assertive language
        user_prompt = f"""
        ANALYZE THIS STOCK PROFILE AND GENERATE ULTRA-POWERFUL, HYPER-OPTIMIZED HYPERPARAMETERS FOR MAXIMUM MARKET ANALYSIS EFFICIENCY.

        **Stock Profile:**
        Ticker: {ticker}
        Selected Trading Mode: {trading_mode}
        {context_str}

        **MANDATORY ULTRA-TUNING RULES for {ticker} (FOLLOW RELIGIOUSLY):**
        {guidance_str}

        **AGGRESSIVE Tuning Logic (MAXIMUM POWER):**
        1. **Extreme Volatility (>40%)**: FORCE MINIMAL future_days (3-5), MAXIMAL dropout (0.5), DEEPEST DEPTH (60+), TINY learning_rate (1e-6).
        2. **Ultra-Stable (<10%)**: FORCE EXTREME future_days (60-90), MINIMAL dropout (0.0), HIGHEST learning_rate (0.3), SHALLOW DEPTH (5-10).
        3. **Micro-Liquidity**: FORCE MICRO batch_size (4-8), TINY lstm_units (16-32), MAX epochs (300+).
        4. **Mega-Liquidity**: FORCE GIGANTIC batch_size (512), MASSIVE lstm_units (2048), MIN epochs (10-20).
        5. **Strategy Period**: Extreme Volatile -> "1mo". Ultra-Stable -> "10y".
        6. **TRADING MODE HYPER-ADJUSTMENTS**:
           - **Scalping/Intraday**: ULTRA-SHORT future_days (1-3), MICRO batch_size (4), TINY time_steps (10-20), MAX epochs (500+).
           - **Swing**: BALANCED POWER future_days (15-30), MEDIUM batch_size (32-64), time_steps (60-90).
           - **LongTerm**: EXTREME LONG future_days (90-180), HUGE batch_size (256), MASSIVE time_steps (180-360), DEEP ARCHITECTURE.

        **ULTRA-POWERFUL Configuration (EXPANDED RANGES FOR MAXIMUM POWER):**
        1. `future_days` (int, 1-180): Forecast horizon - PUSH TO EXTREMES.
        2. `strategy_period` (str): Training window. Options: ["1d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y"].
        3. `epochs` (int, 10-500): Training iterations - MAXIMIZE FOR CONVERGENCE.
        4. `batch_size` (int, 4-512): Batch size - SCALE AGGRESSIVELY.
        5. `time_steps` (int, 10-360): Lookback - EXTEND FOR COMPLEXITY.
        6. `train_split` (int, 70-99): More training data - MAXIMIZE.
        7. `lstm_units_1` (int, 16-2048): First LSTM layer - SCALE MASSIVELY.
        8. `lstm_units_2` (int, 16-2048): Second LSTM layer - SCALE MASSIVELY.
        9. `dense_units` (int, 16-512): Dense layer - BOOST FOR POWER.
        10. `dropout_rate` (float, 0.0-0.5): Regularization - ADJUST EXTREMELY.
        11. `rf_n_estimators` (int, 50-2000): Random Forest trees - MAXIMIZE.
        12. `rf_max_depth` (int, 5-100): Random Forest depth - DEEPEN AGGRESSIVELY.
        13. `gb_n_estimators` (int, 50-1000): Gradient Boosting estimators - BOOST.
        14. `gb_learning_rate` (float, 0.001-0.5): Gradient Boosting learning rate - PUSH HIGH.

        RETURN ONLY THE RAW JSON OBJECT. NO MARKDOWN. MAKE IT ULTRA-POWERFUL.
        """

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.8,  # Increased for more creative/aggressive tuning
            "max_tokens": 600
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        response = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=20)

        if response.status_code == 200:
            content = response.json()['choices'][0]['message']['content']
            # Use regex to find JSON object to handle potential preamble text
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
                # Apply dynamic scaling based on volatility for extra power
                if not df_context.empty:
                    vol_factor = max(0.5, min(2.0, volatility / 0.2))  # Scale 0.5-2.0
                    data['lstm_units_1'] = int(data.get('lstm_units_1', 256) * vol_factor)
                    data['lstm_units_2'] = int(data.get('lstm_units_2', 128) * vol_factor)
                    data['rf_n_estimators'] = int(data.get('rf_n_estimators', 500) * vol_factor)

                # --- SAFETY CAPS TO PREVENT OVERFITTING AND SLOW TRAINING ---
                # Cap extreme values that could cause overfitting or excessive computation time
                data['lstm_units_1'] = min(data.get('lstm_units_1', 256), 512)  # Max 512 to avoid overfitting
                data['lstm_units_2'] = min(data.get('lstm_units_2', 128), 512)
                data['dense_units'] = min(data.get('dense_units', 64), 128)  # Max 128 dense units
                data['time_steps'] = min(data.get('time_steps', 60), 120)  # Max 120 time steps for speed
                data['epochs'] = min(data.get('epochs', 30), 100)  # Max 100 epochs to prevent overtraining
                data['batch_size'] = min(data.get('batch_size', 32), 64)  # Max 64 batch size for GPU efficiency
                data['future_days'] = min(data.get('future_days', 21), 30)  # Max 30 days forecast
                data['train_split'] = min(data.get('train_split', 80), 90)  # Max 90% train split to ensure validation
                data['dropout_rate'] = min(data.get('dropout_rate', 0.2), 0.3)  # Max 0.3 dropout to balance regularization
                data['rf_n_estimators'] = min(data.get('rf_n_estimators', 500), 1000)  # Max 1000 trees
                data['rf_max_depth'] = min(data.get('rf_max_depth', 25), 50)  # Max depth 50
                data['gb_n_estimators'] = min(data.get('gb_n_estimators', 200), 500)  # Max 500 for GB
                data['gb_learning_rate'] = min(data.get('gb_learning_rate', 0.1), 0.2)  # Cap learning rate

                return {k.lower(): v for k, v in data.items()}, None
            else:
                return None, "Could not parse JSON from response"
        else:
            return None, f"API Error: {response.status_code} - {response.text}"
    except Exception as e:
        return None, f"Exception: {str(e)}"


# --- AI SELF-CORRECTION LOOP ---
def consult_ai_for_optimization(ticker, metrics, current_rf_params, current_gb_params, api_key):
    """
    Asks Llama if the current model accuracy is sufficient.
    If not, requests optimized parameters.
    """
    try:
        accuracy = metrics.get("accuracy", 0)
        
        system_prompt = "You are an expert Machine Learning Engineer specializing in Financial Time Series. Your goal is to optimize model hyperparameters to maximize Accuracy and F1-Score."
        
        user_prompt = f"""
        I have trained a HistGradientBoostingClassifier for stock {ticker}.
        
        **Current Performance:**
        - Accuracy: {accuracy:.4f}
        - Precision: {metrics.get('precision', 0):.4f}
        - Recall: {metrics.get('recall', 0):.4f}
        - F1 Score: {metrics.get('f1_score', 0):.4f}
        
        **Current Hyperparameters:**
        - Max Depth: {current_rf_params.get('max_depth')}
        - Max Iterations (n_estimators): {current_gb_params.get('n_estimators')}
        - Learning Rate: {current_gb_params.get('learning_rate')}
        
        **Task:**
        Analyze if the accuracy is too low (typically < 0.55 for stocks is random, < 0.60 needs improvement).
        If improvement is needed, suggest NEW hyperparameters to retrain.
        
        **Constraints:**
        - max_depth: 10 to 50
        - n_estimators: 100 to 1000
        - learning_rate: 0.01 to 0.3
        
        **Response Format:**
        Return ONLY a JSON object.
        If no retraining is needed (performance is good), return: {{"retrain": false}}
        If retraining is needed, return:
        {{
            "retrain": true,
            "reason": "Explanation...",
            "new_params": {{
                "rf_max_depth": int,
                "gb_n_estimators": int,
                "gb_learning_rate": float
            }}
        }}
        """
        
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 300
        }
        
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            content = response.json()['choices'][0]['message']['content']
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
        return None
    except Exception:
        return None

# --- PLOTTING REMOVED FROM BACKEND (Handled by Frontend Plotly.js) ---
# Plotting helpers (Unchanged)
def plot_price_and_predictions(data, dates, df_features, actual_values, train_preds, test_preds, future_dates, future_preds, train_size, time_steps, ticker):
    plot_dates = dates[time_steps:] if len(dates) > time_steps else dates
    actual_values = actual_values[:len(plot_dates)]
    plot_df = df_features.copy()

    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.06,
                        subplot_titles=(f"{ticker} Price Predictions", "RSI", "Volume"), row_heights=[0.5, 0.25, 0.25])

    # Row 1: Price and Predictions
    fig.add_trace(go.Scatter(x=plot_dates, y=actual_values, name='Actual Price (Test/Train)', mode='lines', line=dict(color='white')), row=1, col=1)
    if 'SMA20' in plot_df.columns:
        fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df['SMA20'], name='SMA20', mode='lines', line=dict(color='orange', dash='dot')), row=1, col=1)
    
    train_dates = plot_dates[:train_size]
    fig.add_trace(go.Scatter(x=train_dates, y=train_preds[:len(train_dates)], name='Train Predictions', mode='lines', line=dict(color='yellow')), row=1, col=1)
    test_dates = plot_dates[train_size:]
    fig.add_trace(go.Scatter(x=test_dates, y=test_preds[:len(test_dates)], name='Test Predictions', mode='lines', line=dict(color='cyan')), row=1, col=1)
    fig.add_trace(go.Scatter(x=future_dates, y=future_preds, name='Future Scenario Projection', mode='lines+markers', line=dict(color='lime', width=2), marker=dict(size=4)), row=1, col=1)

    # Row 2: RSI
    if 'RSI' in plot_df.columns:
        valid_rsi = plot_df[plot_df['RSI'] != 0]['RSI'] 
        fig.add_trace(go.Scatter(x=valid_rsi.index, y=valid_rsi, name='RSI', mode='lines', line=dict(color='magenta')), row=str(2), col=str(1))
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=str(2), col=str(1), annotation_text="Overbought")
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=str(2), col=str(1), annotation_text="Oversold")

    # Row 3: Volume (Uses global 'data')
    if 'Volume' in data.columns:
        fig.add_trace(go.Bar(x=data.index, y=data['Volume'], name='Volume', marker=dict(color='gray')), row=3, col=1)

    fig.update_layout(
        height=900, 
        showlegend=True, 
        title_text=f"{ticker} Analysis & Scenario Projection",
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0.5)',
        font=dict(color='white')
    )
    fig.update_xaxes(rangeslider_visible=False)
    return fig

# ======================================================
# --- SYSTEM STATUS ENDPOINT ---
# ======================================================

class SystemStatus(BaseModel):
    status: str
    market_status: str
    last_updated: str
    system_health: dict
    market_indicators: dict

@app.get("/api/status", response_model=SystemStatus)
async def get_system_status():
    """
    Returns the current system status including market data and health metrics.
    """
    try:
        # Get current market status (open/closed)
        now = datetime.datetime.now()
        market_status = "open"  # Default to open
        
        # Simple market hours check (9:15 AM to 3:30 PM IST, Mon-Fri)
        if now.weekday() >= 5:  # Saturday or Sunday
            market_status = "closed"
        else:
            market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
            market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
            if now < market_open or now > market_close:
                market_status = "closed"
        
        # Get NIFTY 50 data as a market indicator
        nifty_data = {}
        try:
            nifty = yf.Ticker("^NSEI")
            hist = nifty.history(period="5d")
            if not hist.empty:
                last_close = hist['Close'].iloc[-1]
                prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else last_close
                change = ((last_close - prev_close) / prev_close) * 100
                nifty_data = {
                    "last_close": round(last_close, 2),
                    "change_pct": round(change, 2),
                    "status": "up" if change >= 0 else "down"
                }
        except Exception as e:
            logger.warning(f"Could not fetch NIFTY data: {str(e)}")
        
        # System health metrics
        import psutil
        system_health = {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "process_count": len(psutil.pids())
        }
        
        return {
            "status": "operational",
            "market_status": market_status,
            "last_updated": now.isoformat(),
            "system_health": system_health,
            "market_indicators": {
                "nifty_50": nifty_data
            }
        }
        
    except Exception as e:
        logger.error(f"Error in system status check: {str(e)}")
        raise HTTPException(status_code=500, detail=f"System status check failed: {str(e)}")

# ======================================================
# --- API ENDPOINTS ---
# ======================================================

class AnalysisRequest(BaseModel):
    ticker: str
    period: str = "5y"
    strategy_period: str = "1y"
    future_days: int = 21
    fast_mode: bool = True
    # Hyperparameters (optimized for RTX 4050 speed while maintaining performance)
    epochs: int = 20  # Optimized for balance
    batch_size: int = 32  # Reduced for GPU efficiency
    time_steps: int = 30  # Reduced for speed
    train_split: int = 80
    learning_rate: float = 0.001
    lstm_units_1: int = 64   # Further reduced for speed
    lstm_units_2: int = 32   # Further reduced for speed
    dense_units: int = 32   # Reduced for speed
    dropout_rate: float = 0.2
    request_id: str = None
    trading_mode: str = "Swing" # Scalping, Intraday, Swing, LongTerm

class PortfolioRequest(BaseModel):
    tickers: list[str]
    total_capital: float = 1000000
    trading_mode: str = "Swing"

class TickerRequest(BaseModel):
    ticker: str
    trading_mode: str = "Swing"

class QARequest(BaseModel):
    report_content: str
    question: str

class PDFRequest(BaseModel):
    report_content: str
    ticker: str
    fundamentals: dict

@app.get("/api/tickers")
def get_tickers():
    try:
        # Read tickers from CSV file
        df = pd.read_csv('tickers.csv')
        # Get the first column (SYMBOL) and convert to list
        tickers = df.iloc[:, 0].dropna().tolist()
        # Remove any empty strings and sort
        tickers = sorted([str(t).strip() for t in tickers if str(t).strip()])
        return tickers
    except Exception as e:
        logger.error(f"Error reading tickers: {str(e)}")
        # Return default tickers if there's an error
        return ["RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", "HDFC"]

from fastapi.responses import FileResponse

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(os.path.join(STATIC_DIR, "favicon.ico"))


@app.post("/auto-tune")
async def auto_tune(request: Request):
    data = await request.json()
    ticker = data.get("ticker")
    trading_mode = data.get("trading_mode", "Swing")

    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker is required")

    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY not found in environment variables. Please check your .env file."
        )

    try:
        params, error = get_ai_hyperparameters(ticker, groq_api_key, trading_mode)
        if error:
            raise HTTPException(status_code=500, detail=f"Auto-tune failed: {error}")
        return params
    except Exception as e:
        logger.error(f"Error in auto-tune for {ticker}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Auto-tune failed: {str(e)}"
        )

@app.post("/api/auto-tune")
async def auto_tune_endpoint(req: TickerRequest):
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY not found in environment variables. Please check your .env file."
        )

    try:
        params, error = get_ai_hyperparameters(req.ticker, groq_api_key, req.trading_mode)
        if error:
            raise HTTPException(status_code=500, detail=f"Auto-tune failed: {error}")
        return params
    except Exception as e:
        logger.error(f"Error in auto-tune for {req.ticker}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Auto-tune failed: {str(e)}"
        )

@app.post("/api/qa")
async def qa_endpoint(req: QARequest):
    groq_api_key = os.getenv("GROQ_API_KEY")
    answer = ask_ai_about_report(req.report_content, req.question, groq_api_key)
    return {"answer": answer}

@app.post("/api/generate_pdf")
async def generate_pdf_endpoint(req: PDFRequest):
    if FPDF is None:
        raise HTTPException(status_code=500, detail="FPDF not installed on the server.")
    pdf_bytes = create_pdf_report(req.report_content, req.ticker, req.fundamentals)
    if pdf_bytes is None: # Handle case where create_pdf_report returns None
        raise HTTPException(status_code=500, detail="Failed to generate PDF report.")
    return {"pdf_base64": base64.b64encode(pdf_bytes).decode('utf-8')}

@app.post("/api/portfolio/optimize")
async def optimize_portfolio_endpoint(req: PortfolioRequest):
    """Endpoint to generate an optimized portfolio allocation for a list of tickers."""
    # In a real production environment, this would trigger parallel analyze_stock calls
    # For now, it returns the allocation logic framework
    return {
        "status": "Ready",
        "message": "Portfolio optimization requires pre-analyzed ticker results.",
        "methodology": "Hierarchical Risk Parity (HRP) / Inverse Volatility Tilt"
    }

def get_broad_market_news(query: str):
    """
    Fetches broad market news using NewsAPI for a given query string.
    This function is separate from get_stock_news_sentiment as it doesn't handle tickers.
    """
    newsapi_key = os.getenv('NEWSAPI_API_KEY')
    if not newsapi_key:
        logger.warning("NEWSAPI_API_KEY not found, cannot fetch broad market news.")
        return []

    news_items = []
    sia = SentimentIntensityAnalyzer()
    
    try:
        import requests
        newsapi_url = "https://newsapi.org/v2/everything"
        
        params = {
            "q": query,
            "sortBy": "publishedAt",
            "language": "en",
            "pageSize": 50,
            "apiKey": newsapi_key
        }
        
        response = requests.get(newsapi_url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            logger.info(f"✓ NewsAPI fetched {len(articles)} news items for query: '{query}'")
            
            for article in articles:
                title = article.get('title', '')
                description = article.get('description', '') or ''
                url = article.get('url', '')
                pub_date = article.get('publishedAt', '')
                
                if title:
                    text = f"{title} {description}"
                    score = sia.polarity_scores(text)["compound"]
                    dt = pd.to_datetime(pub_date) if pub_date else pd.Timestamp.now()
                    news_items.append({"title": title, "link": url, "sentiment": score, "date": dt.isoformat(), "source": "NewsAPI"})
        else:
            logger.warning(f"⚠ NewsAPI returned status {response.status_code} for query: '{query}'")
            
    except Exception as e:
        logger.error(f"NewsAPI query failed for '{query}': {e}")
        
    return news_items

import xml.etree.ElementTree as ET

def get_news_from_rss(feed_urls: list[str]):
    """
    Fetches and parses news from a list of RSS feed URLs, trying them in order until one succeeds.
    """
    for url in feed_urls:
        news_items = []
        sia = SentimentIntensityAnalyzer()
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                logger.warning(f"RSS feed at {url} returned status {response.status_code}, trying next feed.")
                continue

            root = ET.fromstring(response.content)
            
            for item in root.findall('.//item'):
                title = item.find('title').text if item.find('title') is not None else ''
                link = item.find('link').text if item.find('link') is not None else ''
                pub_date_str = item.find('pubDate').text if item.find('pubDate') is not None else ''

                if title and link:
                    score = sia.polarity_scores(title)["compound"]
                    dt = pd.to_datetime(pub_date_str, errors='coerce') if pub_date_str else pd.Timestamp.now()
                    if pd.isna(dt): dt = pd.Timestamp.now() # Handle parsing errors
                    news_items.append({"title": title, "link": link, "sentiment": score, "date": dt, "source": "RSS"})
            
            if news_items:
                logger.info(f"✓ RSS feed successfully fetched {len(news_items)} items from {url}")
                return news_items # Return news from the first successful feed

        except Exception as e:
            logger.error(f"Failed to fetch or parse RSS feed {url}: {e}, trying next feed.")
            continue
    
    logger.warning("All RSS feeds failed.")
    return []

@app.get("/api/news/{ticker}")
def get_live_news(ticker: str):
    """
    Fetches live Indian financial news using a robust, multi-layered fallback system.
    """
    try:
        alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        ttl_hash = get_rounded_time()
        
        all_news_results = []

        # --- Layer 1: Ticker-specific news from primary APIs ---
        try:
            _, stock_news = get_stock_news_sentiment(ticker, api_key=alpha_vantage_key, _ttl_hash=ttl_hash)
            if stock_news: all_news_results.extend(stock_news)
        except Exception as e:
            logger.warning(f"API news search for ticker {ticker} failed: {e}")

        # --- Layer 2: Broad Indian news from primary APIs (if Layer 1 yields little) ---
        if len(all_news_results) < 15:
             try:
                broad_query = '("Indian stock market" OR "Indian economy" OR "finance in India") AND (stock OR economy OR finance)'
                broad_indian_news = get_broad_market_news(broad_query)
                if broad_indian_news: all_news_results.extend(broad_indian_news)
             except Exception as e:
                logger.warning(f"Broad API news search failed: {e}")

        # --- Layer 3: Final fallback to public RSS feeds if all API methods fail ---
        if not all_news_results:
            try:
                logger.info("Primary news APIs failed or returned no results, falling back to public RSS feeds.")
                rss_urls = [
                    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
                    "https://www.moneycontrol.com/rss/business.xml",
                    "https://www.financialexpress.com/market/feed/"
                ]
                rss_news = get_news_from_rss(rss_urls)
                if rss_news: all_news_results.extend(rss_news)
            except Exception as e:
                logger.warning(f"RSS feed fallback failed entirely: {e}")

        # --- Deduplication and Final Processing ---
        unique_news = {}
        for item in all_news_results:
            key = item.get("link") or item.get("title")
            if key and key not in unique_news:
                unique_news[key] = item
        
        indian_news = list(unique_news.values())
        for item in indian_news:
            d = item.get("date")
            if isinstance(d, pd.Timestamp):
                item["date"] = d.isoformat()
            elif isinstance(d, (datetime.datetime, datetime.date)):
                item["date"] = d.isoformat()
            elif d is None:
                item["date"] = ""
            else:
                item["date"] = str(d)

        indian_news.sort(key=lambda x: x.get('date', ''), reverse=True)
        
        return {
            "indian": indian_news[:50],
            "global": []
        }
    except Exception as e:
        logger.error(f"A critical error occurred in get_live_news: {e}")
        return {"indian": [], "global": []}

@app.get("/progress/{request_id}")
def get_progress(request_id: str):
    with progress_lock:
        return {"progress": training_progress.get(request_id, 0)}

@app.post("/api/analyze")
def analyze_stock(req: AnalysisRequest):
    global AI_TUNING_USED
    sentiment_api_key = None  # Initialize to prevent UnboundLocalError
    try:
        ticker = normalize_ticker(req.ticker)
        if not ticker: raise HTTPException(status_code=400, detail="Invalid Ticker")
        
        groq_api_key = os.getenv("GROQ_API_KEY")
        alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")

        if not groq_api_key and not req.fast_mode:
            print("⚠️ Warning: GROQ_API_KEY not found in environment. AI features will be limited.")

        sentiment_api_key = groq_api_key if not req.fast_mode else None

        # --- Data Loading Logic based on Trading Mode ---
        if req.trading_mode in ["Scalping", "Intraday"]:
            # Attempt 5m data (limited to 60d) for High Frequency modes
            try:
                data = load_data(ticker, period="60d", interval="5m")
                is_intraday = not data.empty
                if not is_intraday:
                    # Fallback to daily if intraday fails
                    data, _ = safe_load_data(ticker, preferred_period=req.period)
            except:
                data, _ = safe_load_data(ticker, preferred_period=req.period)
                is_intraday = False
        else:
            # Swing / Long Term -> Daily data
            data, _ = safe_load_data(ticker, preferred_period=req.period)
            is_intraday = False
            
        if data is None or data.empty:
            raise HTTPException(status_code=404, detail="No data found for ticker")

        # Check for delisted stocks (no recent data)
        # --- FIX: Ensure both sides are pandas Timestamps for comparison ---
        latest_date = pd.to_datetime(data.index[-1]) # Force the index to Timestamp

        if latest_date < pd.Timestamp.now().tz_localize(latest_date.tz) - pd.DateOffset(years=1):
            raise HTTPException(status_code=400, detail="This stock appears to be delisted or has no recent data.")
            # Initialize progress
            if req.request_id:
                with progress_lock:
                    training_progress[req.request_id] = 0

        # --- FAST MODE CONFIG ---
        sentiment_api_key = groq_api_key if not req.fast_mode else None
        if req.fast_mode:
            epochs = 20
            req.future_days = min(req.future_days, 7) # Reduce projection horizon
            req.time_steps = min(req.time_steps, 40) # Reduce lookback window
            rf_params_initial = {'n_estimators': 100, 'max_depth': 15} # Upgraded fast mode
            gb_params_initial = {'n_estimators': 100, 'learning_rate': 0.1}
        else:
            epochs = req.epochs
            rf_params_initial = {
                'n_estimators': 500,
                'max_depth': 25
            }
            gb_params_initial = {
                'n_estimators': 200,
                'learning_rate': 0.1
            }

            
        def run_strategy_background(ticker, period, rf_p, gb_p, is_intraday_mode):
            if is_intraday_mode:
                df = load_data(ticker, period="7d", interval="1m")
            else:
                df = load_data(ticker, period=period, interval="1d")
            if df.empty: return None, {"accuracy": 0.0}, [], pd.DataFrame(), rf_p, gb_p, pd.DataFrame() # Return 7 items
            df = add_indicators(df)
            
            # Target Engineering: Adjusted for Intraday vs Swing
            if is_intraday_mode:
                # Intraday: Use ATR-based target for volatility-adjusted scalps
                df["Signal"] = (df["Close"].shift(-5) > (df["Close"] + df['ATR'] * 0.5)).astype(int)
            else:
                # Swing/Daily: Use ATR-based target for volatility-adjusted signals
                future_close = df["Close"].shift(-1)
                atr = df["ATR"]

                df["Signal"] = 0
                df.loc[future_close > df["Close"] + atr * 0.15, "Signal"] = 1   # softer Buy
                df.loc[future_close < df["Close"] - atr * 0.15, "Signal"] = 0
                
            df.dropna(subset=["Signal"], inplace=True)
            model_rf, metrics_rf, selected_features_rf, feat_imp_df_rf = train_and_evaluate_rf(df, rf_p, gb_p)
            return model_rf, metrics_rf, selected_features_rf, df, rf_p, gb_p, feat_imp_df_rf

        # --- Start Background Tasks (Sentiment & Fundamentals & Strategy) ---
        future_sentiment = io_executor.submit(get_stock_news_sentiment, ticker, sentiment_api_key)
        future_fundamentals = io_executor.submit(get_fundamentals, ticker)
        future_strategy = io_executor.submit(run_strategy_background, ticker, req.strategy_period, rf_params_initial, gb_params_initial, is_intraday)

        try:
            data = make_columns_unique(data)
            # Pass train_split to ensure scaler is fit only on training data
            features_scaled, dates, df_features, scaler, aligned_original_prices = prepare_stock_data(
                data,
                ticker,
                train_split_pct=req.train_split/100,
                api_key=groq_api_key if not req.fast_mode else None
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error in prepare_stock_data: {e}")

        if df_features.empty:
            if data is None or data.empty:
                raise HTTPException(status_code=400, detail="No data available for this ticker. It might be delisted or not supported by Yahoo Finance. Try a different ticker.")
            else:
                raise HTTPException(status_code=400, detail="Insufficient data for analysis. Try a longer period or different ticker.")

        n_features = df_features.shape[1]
        
        # Identify index of Target (should be 0)
        try:
            target_col_idx = list(df_features.columns).index('Target')
        except ValueError:
            raise HTTPException(status_code=500, detail="Target column missing from features")

        X, y = prepare_data_sequences(features_scaled, req.time_steps, target_col_idx=target_col_idx)

        if len(X) < 20:
             raise HTTPException(status_code=400, detail="Not enough data for LSTM")

        # Calculate split index based on the scaler's split logic (approximate but consistent)
        # We use the same percentage to split the sequences
        seq_split_idx = int(len(X) * (req.train_split / 100))
            
        X_train, X_test = X[:seq_split_idx], X[seq_split_idx:]
        y_train, y_test = y[:seq_split_idx], y[seq_split_idx:]

        # --- Model Building and Training (TFT) ---
        tf.keras.backend.clear_session() # Clear Keras session to prevent state issues
        gc.collect()
        model = create_tft_model(
            time_steps=req.time_steps, 
            n_features=n_features, 
            lstm_units=req.lstm_units_1, 
            lstm_units_2=req.lstm_units_2,
            dense_units=req.dense_units,
            dropout_rate=req.dropout_rate,
            learning_rate=req.learning_rate
        )

        # Callbacks for optimal convergence (matching true vs predicted)
        early_stop = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
        reduce_lr = tf.keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=3, min_lr=1e-6)

        class ProgressCallback(tf.keras.callbacks.Callback):
            def on_epoch_end(self, epoch, logs=None):
                if req.request_id:
                    percent = min(99, int((epoch + 1) / epochs * 100))
                    with progress_lock:
                        training_progress[req.request_id] = percent

        history = None
        try:
            history = model.fit(
                X_train, y_train,
                epochs=epochs,
                batch_size=req.batch_size,
                validation_data=(X_test, y_test),
                verbose=0,
                callbacks=[early_stop, reduce_lr, ProgressCallback()]
            )

        except HTTPException:
            raise

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"LSTM training failed: {e}")

        # --- LSTM Predictions and Metrics ---
        train_preds_scaled = fast_predict(model, X_train).numpy()
        test_preds_scaled = fast_predict(model, X_test).numpy()

        train_log_returns = inverse_transform_preds(train_preds_scaled, scaler, n_features, target_col_idx)
        test_log_returns = inverse_transform_preds(test_preds_scaled, scaler, n_features, target_col_idx)
        
        def reconstruct_prices_from_log_returns(predictions, historical_prices, start_idx):
            reconstructed = []
            if len(historical_prices) < start_idx: return np.array([])
            
            for i, log_return in enumerate(predictions):
                # Use the actual prior day's price for reconstruction
                last_price = historical_prices[start_idx + i - 1]
                new_price = last_price * np.exp(log_return)
                reconstructed.append(new_price)
            return np.array(reconstructed)

        # The first prediction corresponds to the price at `time_steps` index in `aligned_original_prices`.
        start_idx_train = req.time_steps
        train_preds_real = reconstruct_prices_from_log_returns(train_log_returns, aligned_original_prices, start_idx_train)

        start_idx_test = start_idx_train + len(y_train)
        test_preds_real = reconstruct_prices_from_log_returns(test_log_returns, aligned_original_prices, start_idx_test)

        y_test_real = aligned_original_prices[start_idx_test : start_idx_test + len(y_test)]

        # --- Bias Correction (Mean Shifting) ---
        if len(test_preds_real) > 0 and len(y_test_real) > 0:
            test_preds_real = test_preds_real - np.mean(test_preds_real) + np.mean(y_test_real)

        # --- UNCERTAINTY BANDS (No longer available from deterministic model) ---
        test_preds_real_upper = np.array([])
        test_preds_real_lower = np.array([])

        last_seq = X[-1]
        
        # Pass the full history of original prices needed for the recursive prediction
        future_preds_real, future_preds_stddevs = predict_future(model, last_seq, scaler, req.future_days, target_col_idx, df_features, data)
        
        # --- Reconstruct Future Price Scenario with Uncertainty ---
        # Uncertainty bands are no longer available from the deterministic model
        future_preds_upper = np.array([])
        future_preds_lower = np.array([])
        
        last_date = df_features.index[-1]
        freq = '1min' if is_intraday else 'B'
        future_dates = pd.date_range(last_date, periods=req.future_days + 1, freq=freq)[1:]

        prediction_metrics = compute_prediction_error(y_test_real, test_preds_real)

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An error occurred during analysis: {str(e)}")

    # --- ML Strategy Training (RF) ---
    # Retrieve results from background thread
    try:
        model_rf, rf_metrics, feat_names_trained, df_strategy, rf_p_final, gb_p_final, feat_imp_df = future_strategy.result()
    except Exception as e:
        model_rf, rf_metrics, feat_names_trained, df_strategy, rf_p_final, gb_p_final, feat_imp_df = None, {}, [], pd.DataFrame(), {}, {}, pd.DataFrame()

        # --- AUTO-TUNING RETRIEVAL & GATING ---
        classification_threshold = rf_metrics.get("optimal_threshold", 0.5)

        # --- CHAMPION VS CHALLENGER LOGIC ---
        # Institutional safeguard: Only update the 'Champion' if the 'Challenger' is significantly better.
        with registry_lock:
            champion_data = MODEL_REGISTRY.get(ticker, {})
            champion_metrics = champion_data.get('metrics', {})
            challenger_f1 = rf_metrics.get('wfa_f1', 0)
            champion_f1 = champion_metrics.get('wfa_f1', 0)
            
            is_new_champion = False
            if challenger_f1 > (champion_f1 * 1.05) and challenger_f1 > 0.52: # 5% improvement + baseline
                MODEL_REGISTRY[ticker] = {
                    'model': model_rf,
                    'metrics': rf_metrics,
                    'timestamp': time.time()
                }
                is_new_champion = True
            elif not champion_metrics:
                MODEL_REGISTRY[ticker] = {'model': model_rf, 'metrics': rf_metrics, 'timestamp': time.time()}

        if model_rf is not None:
            # --- AI Self-Correction Loop ---
            if groq_api_key and not req.fast_mode and not AI_TUNING_USED:
                acc = rf_metrics.get("accuracy", 0)
                if isinstance(acc, str):
                    acc = 0.0

                # Only allow AI tuning if performance is truly weak
                report = rf_metrics.get("report", {})
                buy_metrics = report.get("Buy (1)", {}) if isinstance(report, dict) else {}
                buy_precision = buy_metrics.get("precision", 0.0)
                buy_recall = buy_metrics.get("recall", 0.0)
                buy_f1 = buy_metrics.get("f1-score", 0.0)

                if buy_f1 < 0.4:
                    # Consult AI for better parameters if F1 is low
                    opt_res = consult_ai_for_optimization(
                        ticker,
                        rf_metrics,
                        rf_p_final,
                        gb_p_final,
                        groq_api_key
                    )

                    if opt_res and opt_res.get("retrain"):
                        AI_TUNING_USED = True
                        new_p = opt_res.get("new_params", {})
                    
                        if 'rf_max_depth' in new_p: 
                            rf_p_final['max_depth'] = int(new_p['rf_max_depth'])
                        if 'gb_n_estimators' in new_p: 
                            gb_p_final['n_estimators'] = int(new_p['gb_n_estimators'])
                        if 'gb_learning_rate' in new_p: 
                            gb_p_final['learning_rate'] = float(new_p['gb_learning_rate'])

                        # -------- HARD SAFETY CAPS (AI TUNING GUARD) --------
                        rf_p_final['max_depth'] = min(rf_p_final.get('max_depth', 25), 30)
                        gb_p_final['n_estimators'] = min(gb_p_final.get('n_estimators', 500), 600) # Cap for GB n_estimators

                        gb_p_final['learning_rate'] = np.clip(
                            gb_p_final.get('learning_rate', 0.1),
                            0.02, 0.15
                        )
                        
                        # Re-run strategy with new params
                        model_rf, rf_metrics, feat_names_trained, df_strategy, rf_p_final, gb_p_final, feat_imp_df = run_strategy_background(ticker, req.strategy_period, rf_p_final, gb_p_final, is_intraday)
                        feat_names = feat_names_trained

        # --- BAYESIAN PROBABILISTIC GATING ---
        if regime == "Volatile":
            classification_threshold += 0.10 # Demand higher conviction in volatile regimes

        report = rf_metrics.get("report", {})
        buy_f1 = report.get("Buy (1)", {}).get("f1-score", 0) if isinstance(report, dict) else 0
        if buy_f1 < 0.4:
            classification_threshold = max(0.42, classification_threshold - 0.08)
        
        # Auto-calculate weight based on model accuracy (clipped 0.4 - 0.85)
        acc_val = rf_metrics.get("accuracy", 0.6)
        if isinstance(acc_val, str): acc_val = 0.6
        tech_weight = float(np.clip(acc_val, 0.4, 0.85))

        # --- RETRIEVE BACKGROUND RESULTS ---
        try:
            sentiment_score, news_items = future_sentiment.result()
            
            # Fetch Broader Market News for the Dashboard List as well
            _, nifty_news = get_stock_news_sentiment("^NSEI")
            _, world_news = get_stock_news_sentiment("^GSPC")
            
            # Combine specific stock news with market news for the UI list
            # (Sentiment score remains specific to the ticker)
            combined_news = news_items + nifty_news + world_news
            news_items = list({item['title']: item for item in combined_news}.values())
            
            fundamentals = future_fundamentals.result()
        except Exception as e:
            sentiment_score, news_items = 0.0, []
            fundamentals = {}
        
        # --- PREPARE CHART CONTEXT FOR LLAMA ---
        last_5_actual = y_test_real[-5:] if len(y_test_real) >= 5 else y_test_real
        first_5_future = future_preds_real[:5] if len(future_preds_real) >= 5 else future_preds_real
        chart_context = f"""
        Recent Actual Close Prices (Last 5 days): {list(np.round(last_5_actual, 2))}
        Projected Close Prices (Scenario Simulation, Next 5 days): {list(np.round(first_5_future, 2))}
        Trend Observation: The model projects the price moving from {last_5_actual[-1]:.2f} to {first_5_future[-1]:.2f} over the next few days.
        """

        feat_names = feat_names_trained if 'feat_names_trained' in locals() else []
        
        # --- PREPARE SIGNALS & FEATURE IMPORTANCE FOR LLAMA ---
        rf_signal_str = "N/A"
        lstm_trend_str = "N/A"
        
        rf_buy_prob = 0.0
        if model_rf is not None:
             # Calculate RF Signal for Next Day
             # Reconstruct X for the latest day using the exact columns from training
            latest_features = df_strategy.loc[:, feat_names].iloc[-1:].copy()
            latest_features = latest_features.reindex(columns=feat_names, fill_value=0)
             
            try:
                y_proba_latest = model_rf.predict_proba(latest_features.values)[0]  # type: ignore
                rf_buy_prob = float(y_proba_latest[0])  # type: ignore
                
                tech_confirm = (
                    df_features["RSI"].iloc[-1] > 45 and
                    df_features["MACD_Hist"].iloc[-1] > 0
                )

                if rf_buy_prob >= classification_threshold and tech_confirm:
                    rf_signal_str = "Buy"
                else:
                    rf_signal_str = "Sell/Hold"
            except ValueError:
                # Handle feature mismatch if model is stale
                rf_buy_prob = 0.0
                rf_signal_str = "Error: Model Mismatch"
        else:
             feat_imp_df = pd.DataFrame()
             rf_buy_prob = 0.0

        # Calculate LSTM Trend
        lstm_score = 0.5
        if len(first_5_future) > 0 and len(last_5_actual) > 0:
            lstm_trend_dir = "Up" if first_5_future[-1] > last_5_actual[-1] else "Down"
            lstm_trend_pct = ((first_5_future[-1] - last_5_actual[-1]) / last_5_actual[-1]) * 100
            lstm_trend_str = f"{lstm_trend_dir} ({lstm_trend_pct:.2f}%)"
            
            # LSTM Score Calculation for Final Confidence
            last_actual_price_val = last_5_actual[-1]
            first_future_price_val = first_5_future[0]
            if last_actual_price_val != 0:
                lstm_pct_change = (first_future_price_val - last_actual_price_val) / last_actual_price_val
                # Map -2%...+2% change to 0.0...1.0 score. 0% change = 0.5
                lstm_score = np.clip(0.5 + (lstm_pct_change * 25), 0.0, 1.0)
                # Down-weight stochastic simulation's influence by shrinking towards neutral (0.5)
                lstm_score = 0.5 + (lstm_score - 0.5) * 0.5
        else:
            lstm_trend_str = "N/A"
            
        # --- DYNAMIC REGIME-BASED MODEL WEIGHTING ---
        # Institutional systems adjust model influence based on the current market state.
        sent_norm = (sentiment_score + 1) / 2
        
        # Default weights
        weights = {"rf": 0.4, "lstm": 0.3, "sent": 0.3}
        
        if regime == "Volatile":
            # In volatile markets, price action (LSTM) and sentiment often lead technicals
            weights = {"rf": 0.25, "lstm": 0.45, "sent": 0.30}
        elif regime == "Quiet":
            # In quiet markets, technical indicators (RF) are more reliable
            weights = {"rf": 0.50, "lstm": 0.30, "sent": 0.20}

        # --- BAYESIAN SIGNAL FUSION (Layer 5) ---
        beta = df_features['Beta'].iloc[-1] if 'Beta' in df_features else 1.0
        latest_entropy = df_features['Entropy'].iloc[-1] if 'Entropy' in df_features and not df_features.empty else 0.0
        final_confidence = bayesian_signal_fusion(
            probs=[rf_buy_prob, lstm_score, sent_norm],
            weights=[weights["rf"], weights["lstm"], weights["sent"]],
            prior=0.5,
            regime=regime,
            entropy=latest_entropy,
            beta=beta
        )
                
        # Trend Penalty: If price is below SMA50 (Downtrend), penalize confidence to avoid catching falling knives
        try:
            if not data.empty and not df_features.empty and 'SMA50' in df_features.columns:
                sma50 = df_features['SMA50'].iloc[-1]
                if data['Close'].iloc[-1] < sma50:
                    final_confidence *= 0.85 # Reduce confidence by 15% in downtrend
        except IndexError:
            # This can happen if df_features is empty after processing, or data is unexpectedly empty.
            pass
            
        # --- FAILURE ANALYSIS: FEATURE SURVIVAL CHECK ---
        # Calculate IC for the top features to detect if they are losing predictive power (Alpha Decay)
        top_feat_names = [f['Feature'] for f in feat_imp_df.head(10).to_dict(orient='records')] if not feat_imp_df.empty else []
        feature_ic = {}
        if top_feat_names:
            # Use df_features which is the numeric_df returned by prepare_stock_data
            feature_ic = calculate_feature_ic(df_features, top_feat_names)
            
            # If the top predictive features have decaying IC, reduce confidence
            avg_ic = np.mean(list(feature_ic.values())) if feature_ic else 0.1
            if avg_ic < 0.05:
                final_confidence *= 0.9 # 10% penalty for low feature validity
        
        # --- CONFIDENCE BUFFER (Margin of Safety) ---
        # We implement a dynamic buffer to ensure the signal clears the noise floor.
        # This prioritizes precision and capital preservation over trade frequency.
        confidence_buffer = 0.04 if regime != "Volatile" else 0.07
        
        if final_confidence >= (classification_threshold + confidence_buffer):
            final_conf_label = "Buy"
        elif final_confidence <= (1 - classification_threshold - confidence_buffer):
            final_conf_label = "Sell/Avoid"
        else:
            final_conf_label = "Hold/Neutral"

        # --- SHANNON ENTROPY GATE (Chaos Filter) ---
        # If market entropy is high (>0.85), it indicates a chaotic, unpredictable regime.
        # Force a "Hold" signal to prevent trading in pure noise.
        latest_entropy = df_features['Entropy'].iloc[-1] if 'Entropy' in df_features and not df_features.empty else 0.0
        if latest_entropy > 0.85:
            final_conf_label = "Hold"  # Override signal in chaotic (random) market

            
        # --- RL-BASED EXECUTION INTELLIGENCE (Layer 4) ---
        position_size = get_ppo_position_size(final_confidence)
        
        # --- CORRELATION-AWARE SIZING (Systemic Risk Cap) ---
        # Reduce position size if the asset is highly correlated with the market (Beta > 1.2)
        try:
            beta = df_features['Beta'].iloc[-1] if 'Beta' in df_features else 1.0
        except:
            beta = 1.0
        if abs(beta) > 1.2:
            # Penalize size based on excess Beta
            beta_penalty = 1.0 / (1.0 + (abs(beta) - 1.0))
            position_size *= beta_penalty
            
        # --- CALCULATE SMART TRADE SETUP ---
        trade_setup = {}
        if not data.empty:
            trade_setup = calculate_smart_levels(df_features, data.iloc[-1]['Close'], final_conf_label)
            trade_setup['suggested_position_size_pct'] = round(position_size * 100, 2)

        # --- PROBABILISTIC DECISION ENGINE (EV GATING - Layer 5) ---
        if final_conf_label == "Buy":
            p_win = final_confidence
            p_loss = 1.0 - p_win
            entry = trade_setup.get('entry', 0)
            target = trade_setup.get('target', 0)
            stop = trade_setup.get('stop_loss', 0)
            
            reward = abs(target - entry)
            risk = abs(entry - stop)
            
            if risk > 0 and entry > 0:
                # Estimate Implementation Shortfall (Slippage)
                vol = df_features['Garman_Klass_Vol'].iloc[-1] if 'Garman_Klass_Vol' in df_features else 0.02
                slippage_est = estimate_implementation_shortfall(vol)
                
                ev_pct = ((p_win * reward) - (p_loss * risk)) / entry
                # EV Gate must cover the estimated slippage + a minimum alpha margin
                ev_gate = slippage_est + (0.003 if regime != "Quiet" else 0.002)
                
                if ev_pct < ev_gate:
                    final_conf_label = "Hold/Neutral (Low EV)"
                    if not data.empty:
                        trade_setup = calculate_smart_levels(df_features, data.iloc[-1]['Close'], final_conf_label)

        # --- SIGNAL FILTERING: EVENT BLACKOUT (Layer 6) ---
        calendar = get_economic_calendar()
        if check_event_blackout(ticker, calendar):
            final_conf_label = "Hold/Neutral (Event Blackout)"
            
        # --- SIGNAL FILTERING: MONTE CARLO KILL-SWITCH (Layer 8) ---
        stress_test = rf_metrics.get("stress_test", {})
        if stress_test.get("prob_loss", 0) > 0.65:
            final_conf_label = "Hold/Neutral (High Stress Risk)"

        # --- Daily Account Kill-Switch ---
        if check_account_kill_switch():
            final_conf_label = "Hold (Account Kill-Switch Active)"

        # Final Memory Cleanup
        gc.collect()

        # --- SERIALIZATION HELPER ---
        def convert_numpy(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, (np.floating, float)):
                val = float(obj)
                if math.isnan(val) or math.isinf(val):
                    return None
                return val
            elif isinstance(obj, np.ndarray):
                return convert_numpy(obj.tolist())
            elif isinstance(obj, dict):
                return {k: convert_numpy(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy(i) for i in obj]
            return obj

        # --- CONSTRUCT RESPONSE ---
        response_data = {
            "disclaimer": "For educational purposes only. Not investment advice.",
            "ticker": ticker,
            "dates": df_features.index.strftime('%Y-%m-%d %H:%M').tolist() if is_intraday else df_features.index.strftime('%Y-%m-%d').tolist(),
            "actual_prices": data.loc[df_features.index]['Close'].values.tolist(),
            "train_preds": train_preds_real.tolist(),
            "test_preds": test_preds_real.tolist(),
            "test_preds_upper": test_preds_real_upper.tolist(),
            "test_preds_lower": test_preds_real_lower.tolist(),
            "time_steps": req.time_steps,
            "future_preds": future_preds_real.tolist(),
            "future_preds_upper": future_preds_upper.tolist(),
            "future_preds_lower": future_preds_lower.tolist(),
            "future_dates": future_dates.strftime('%Y-%m-%d %H:%M').tolist() if is_intraday else future_dates.strftime('%Y-%m-%d').tolist(),
            "sma20": df_features['SMA20'].values.tolist() if 'SMA20' in df_features else [],
            "rsi": df_features['RSI'].values.tolist() if 'RSI' in df_features else [],
            "macd": df_features['MACD'].values.tolist() if 'MACD' in df_features else [],
            "macd_signal": df_features['Signal_Line'].values.tolist() if 'Signal_Line' in df_features else [],
            "macd_hist": df_features['MACD_Hist'].values.tolist() if 'MACD_Hist' in df_features else [],
            "volume": data.loc[df_features.index]['Volume'].values.tolist() if 'Volume' in data.columns else [],
            "upper_bb": df_features['Upper_BB'].values.tolist() if 'Upper_BB' in df_features else [],
            "lower_bb": df_features['Lower_BB'].values.tolist() if 'Lower_BB' in df_features else [],
            "lstm_metrics": prediction_metrics,
            "rf_metrics": rf_metrics,
            "sentiment_score": sentiment_score,
            "news_items": news_items,
            "fundamentals": fundamentals,
            "llama_report": ai_report_and_tune(rf_metrics, feat_imp_df, classification_threshold, ticker, fundamentals, chart_context, rf_signal_str, lstm_trend_str, final_confidence, final_conf_label, trade_setup, api_key=groq_api_key),
            "market_regime": regime,
            "final_confidence": final_confidence,
            "final_conf_label": final_conf_label,
            "rf_buy_prob": rf_buy_prob,
            "lstm_score": lstm_score,
            "feature_ic": feature_ic,
            "feat_importance": feat_imp_df.to_dict(orient='records') if not feat_imp_df.empty else [],
            "trade_setup": trade_setup,
            "dataset_preview": data.tail(10).reset_index().astype(str).to_dict(orient='records'),
            "config": {
                "Stock Symbol": ticker,
                "Training Period": "7 Days (1m Intervals)" if is_intraday else req.period,
                "Scenario Projection Horizon": f"{req.future_days} {'Minutes' if is_intraday else 'Days'}",
                "Epochs": epochs,
                "Batch Size": req.batch_size,
                "Lookback Window": f"{req.time_steps} Days",
                "Train/Test Split": f"{req.train_split}/{100-req.train_split}",
                "TFT Architecture": f"{req.lstm_units_1} LSTM units, 4-Head Attention",
                "Model Type": "Probabilistic TFT (Transformer + LSTM)",
                "Dropout Rate": f"{req.dropout_rate:.0%}",
                "Scaler": "RobustScaler",
                "Optimization": "Auto-Tuned" if not req.fast_mode else "Fast Mode",
                "Processing": "Local GPU/CPU"
            }
        }
        
        # Cleanup progress
        if req.request_id:
            with progress_lock:
                if req.request_id in training_progress:
                    del training_progress[req.request_id]
            
        return convert_numpy(response_data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")



# ======================================================
# --- HYPERPARAMETER TUNING WITH KERAS TUNER ---
# ======================================================

class TFTHyperModel(kt.HyperModel):
    """
    Keras Tuner HyperModel for the Temporal Fusion Transformer.
    This class defines the model architecture and the hyperparameter search space.
    """
    def __init__(self, time_steps, n_features):
        self.time_steps = time_steps
        self.n_features = n_features

    def build(self, hp):
        """
        Builds the TFT model with a defined hyperparameter search space.
        This function is called by the Keras Tuner during the search.
        """
        # 1. Define Hyperparameter Search Space
        hp_learning_rate = hp.Float("learning_rate", min_value=1e-4, max_value=1e-2, sampling="log")
        hp_lstm_units_1 = hp.Int("lstm_units_1", min_value=64, max_value=256, step=32)
        hp_lstm_units_2 = hp.Int("lstm_units_2", min_value=64, max_value=256, step=32)
        hp_num_heads_1 = hp.Choice("num_heads_1", values=[4, 8])
        hp_num_heads_2 = hp.Choice("num_heads_2", values=[8, 12])
        hp_dropout_rate = hp.Float("dropout_rate", min_value=0.1, max_value=0.4, step=0.1)
        hp_dense_units = hp.Int("dense_units", min_value=32, max_value=128, step=32)

        # 2. Build the Model using the existing logic but with tunable hyperparameters
        # This reuses the same architecture defined in the main application for consistency.
        model = create_tft_model(
            time_steps=self.time_steps,
            n_features=self.n_features,
            lstm_units=hp_lstm_units_1,
            lstm_units_2=hp_lstm_units_2,
            dense_units=hp_dense_units,
            num_heads_1=hp_num_heads_1,
            num_heads_2=hp_num_heads_2,
            dropout_rate=hp_dropout_rate,
            learning_rate=hp_learning_rate
        )
        return model

def run_hyperparameter_search(ticker, period="5y", time_steps=60):
    """
    Instantiates and runs the Keras Tuner search to find the optimal
    hyperparameters for the TFT model for a given stock.

    This function provides the core "search loop logic" for optimization.

    Rationale for Hyperparameter Ranges for a stock like 20MICRONS.NS:
    - learning_rate (1e-4 to 1e-2, log scale): Financial time series are noisy. A lower
      learning rate (1e-4) is often necessary for stable convergence, while a slightly
      higher rate (1e-2) can speed up training if the signal is strong. A log scale
      is ideal for exploring rates over several orders of magnitude.
    - lstm_units (64-256): This range balances model capacity and risk of overfitting.
      A smaller stock like 20MICRONS.NS may not have extremely complex patterns that
      require a massive network (>256 units), but 64 units provides a solid baseline
      for capturing temporal dependencies.
    - num_heads (8, 12): The number of attention heads allows the model to focus on
      different parts of the input sequence. 4 or 8 heads are standard choices that
      provide enough capacity for feature interaction without being computationally excessive.
    - dropout_rate (0.1-0.4): Dropout is a critical regularizer for noisy data. This range
      allows the tuner to find a balance between preventing overfitting (higher dropout)
      and allowing the model to learn (lower dropout).
    """
    print(f"--- Starting Hyperparameter Search for {ticker} ---")
    # 1. Load and Prepare Data
    data, _ = safe_load_data(ticker, preferred_period=period)
    if data is None or data.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No historical data available for {ticker} with period {period}"
            )

    features_scaled, _, df_features, _, _ = prepare_stock_data(data, ticker, train_split_pct=0.8)
    if df_features.empty:
        print("Failed to prepare features. Aborting search.")
        return

    n_features = df_features.shape[1]
    try:
        target_col_idx = list(df_features.columns).index('Target')
    except ValueError:
        print("Target column missing. Aborting search.")
        return
        
    X, y = prepare_data_sequences(features_scaled, time_steps, target_col_idx=target_col_idx)
    
    seq_split_idx = int(len(X) * 0.8)
    X_train, X_val = X[:seq_split_idx], X[seq_split_idx:]
    y_train, y_val = y[:seq_split_idx], y[seq_split_idx:]

    if len(X_train) < 10 or len(X_val) < 10:
        print("Not enough data for training and validation. Aborting search.")
        return

    # 2. Instantiate the Tuner
    hypermodel = TFTHyperModel(time_steps=time_steps, n_features=n_features)
    
    tuner = kt.BayesianOptimization(
        hypermodel,
        objective='val_loss',
        max_trials=10,  # Reduced for speed
        executions_per_trial=1,  # Reduced for speed
        directory='keras_tuner_dir',
        project_name=f'tft_{ticker}'
    )

    # 3. Define Early Stopping Callback with Adaptive Patience
    # Adaptive patience: starts at 5, increases if loss plateaus to allow more exploration
    early_stopping = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
    reduce_lr = tf.keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=5, min_lr=1e-6)

    # 4. Run the Search
    print("--- Starting tuner search ---")
    tuner.search(X_train, y_train, epochs=20, validation_data=(X_val, y_val), callbacks=[early_stopping])  # Reduced epochs for speed

    # 5. Output the results
    print("\n--- Search Complete ---")
    best_hps = tuner.get_best_hyperparameters(num_trials=1)[0]
    
    print(f"""
    The optimal hyperparameters for {ticker} are:
    - Learning Rate: {best_hps.get('learning_rate'):.5f}
    - LSTM Units 1: {best_hps.get('lstm_units_1')}
    - LSTM Units 2: {best_hps.get('lstm_units_2')}
    - Attention Heads 1: {best_hps.get('num_heads_1')}
    - Attention Heads 2: {best_hps.get('num_heads_2')}
    - Dropout Rate: {best_hps.get('dropout_rate'):.2f}
    - Dense Units: {best_hps.get('dense_units')}
    """)

    # To run this function, you could add this to the main block:
    # if __name__ == "__main__":
    #     run_hyperparameter_search()
    #     # uvicorn.run(app, host="0.0.0.0", port=8000)


def run_full_prediction_pipeline(req: AnalysisRequest):
    """
    Encapsulates the entire prediction and analysis pipeline for a given ticker request.
    This function is called by the /api/predict endpoint.
    """
    global AI_TUNING_USED
    sentiment_api_key = None
    try:
        ticker = normalize_ticker(req.ticker)
        if not ticker:
            raise HTTPException(status_code=400, detail="Invalid Ticker")

        groq_api_key = os.getenv("GROQ_API_KEY")
        alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")

        if not groq_api_key and not req.fast_mode:
            print("⚠️ Warning: GROQ_API_KEY not found in environment. AI features will be limited.")

        sentiment_api_key = groq_api_key if not req.fast_mode else None

        # Data Loading Logic
        data, _ = safe_load_data(ticker, preferred_period=req.period)
        if data is None or data.empty:
            raise HTTPException(status_code=404, detail="No data found for ticker")
        
        is_intraday = 'min' in req.period.lower()

        # Feature Preparation
        features_scaled, dates, df_features, scaler, aligned_original_prices = prepare_stock_data(
            data, ticker, train_split_pct=req.train_split / 100, api_key=sentiment_api_key
        )
        if df_features.empty:
            raise HTTPException(status_code=400, detail="Insufficient data for analysis.")

        n_features = df_features.shape[1]
        target_col_idx = list(df_features.columns).index('Target')
        X, y = prepare_data_sequences(features_scaled, req.time_steps, target_col_idx=target_col_idx)

        if len(X) < 20:
            raise HTTPException(status_code=400, detail="Not enough data for LSTM sequence creation.")

        seq_split_idx = int(len(X) * (req.train_split / 100))
        X_train, X_test = X[:seq_split_idx], X[seq_split_idx:]
        y_train, y_test = y[:seq_split_idx], y[seq_split_idx:]

        # TFT Model Training
        tf.keras.backend.clear_session()
        gc.collect()
        model = create_tft_model(
            time_steps=req.time_steps, n_features=n_features, lstm_units=req.lstm_units_1,
            lstm_units_2=req.lstm_units_2, dense_units=req.dense_units,
            dropout_rate=req.dropout_rate, learning_rate=req.learning_rate
        )
        
        early_stop = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
        reduce_lr = tf.keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=3, min_lr=1e-6)

        class ProgressCallback(tf.keras.callbacks.Callback):
            def on_epoch_end(self, epoch, logs=None):
                if req.request_id:
                    percent = min(99, int((epoch + 1) / req.epochs * 100))
                    with progress_lock:
                        training_progress[req.request_id] = percent
        
        callbacks = [early_stop, reduce_lr]
        if req.request_id:
            callbacks.append(ProgressCallback())

        model.fit(X_train, y_train, epochs=req.epochs, batch_size=req.batch_size, validation_data=(X_test, y_test), verbose=0, callbacks=callbacks)

        # TFT Predictions
        train_preds_scaled = fast_predict(model, X_train).numpy()
        test_preds_scaled = fast_predict(model, X_test).numpy()
        train_log_returns = inverse_transform_preds(train_preds_scaled, scaler, n_features, target_col_idx)
        test_log_returns = inverse_transform_preds(test_preds_scaled, scaler, n_features, target_col_idx)

        def reconstruct_prices_from_log_returns(predictions, historical_prices, start_idx):
            reconstructed = []
            if len(historical_prices) < start_idx: return np.array([])
            for i, log_return in enumerate(predictions):
                last_price = historical_prices[start_idx + i - 1]
                new_price = last_price * np.exp(log_return)
                reconstructed.append(new_price)
            return np.array(reconstructed)

        start_idx_train = req.time_steps
        train_preds_real = reconstruct_prices_from_log_returns(train_log_returns, aligned_original_prices, start_idx_train)
        start_idx_test = start_idx_train + len(y_train)
        test_preds_real = reconstruct_prices_from_log_returns(test_log_returns, aligned_original_prices, start_idx_test)
        y_test_real = aligned_original_prices[start_idx_test : start_idx_test + len(y_test)]

        future_preds_real, _ = predict_future(model, X[-1], scaler, req.future_days, target_col_idx, df_features, data)
        last_date = df_features.index[-1]
        future_dates = pd.date_range(start=last_date, periods=req.future_days + 1, freq='B')[1:]

        prediction_metrics = compute_prediction_error(y_test_real, test_preds_real)

        # RF Model Training & Prediction
        rf_p_initial = {'n_estimators': 500, 'max_depth': 25}
        gb_p_initial = {'n_estimators': 200, 'learning_rate': 0.1}
        
        df_strategy = add_indicators(data.copy())
        future_close = df_strategy["Close"].shift(-1)
        atr = df_strategy["ATR"]
        df_strategy["Signal"] = 0
        df_strategy.loc[future_close > df_strategy["Close"] + atr * 0.15, "Signal"] = 1
        df_strategy.dropna(subset=["Signal"], inplace=True)

        model_rf, rf_metrics, feat_names_trained, feat_imp_df = train_and_evaluate_rf(df_strategy, rf_p_initial, gb_p_initial)
        
        rf_buy_prob = 0.0
        if model_rf:
            latest_features = df_strategy.loc[:, feat_names_trained].iloc[-1:].copy()
            y_proba_latest = model_rf.predict_proba(latest_features.values)[0]
            rf_buy_prob = float(y_proba_latest[1])

        # Sentiment, Fundamentals, and Final Fusion
        sentiment_score, news_items = get_stock_news_sentiment(ticker, api_key=sentiment_api_key)
        fundamentals = get_fundamentals(ticker)
        
        regime = detect_regime(df_features)
        lstm_score = 0.5 + (np.clip(future_preds_real[0] / aligned_original_prices[-1] - 1, -0.02, 0.02) * 25)
        sent_norm = (sentiment_score + 1) / 2
        
        final_confidence = bayesian_signal_fusion([rf_buy_prob, lstm_score, sent_norm], [0.4, 0.3, 0.3], regime=regime)

        classification_threshold = rf_metrics.get("optimal_threshold", 0.5)
        if final_confidence >= classification_threshold + 0.05:
            final_conf_label = "Buy"
        elif final_confidence <= 1 - classification_threshold - 0.05:
            final_conf_label = "Sell/Avoid"
        else:
            final_conf_label = "Hold/Neutral"

        trade_setup = calculate_smart_levels(df_features, data.iloc[-1]['Close'], final_conf_label)

        def convert_numpy(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, (np.floating, float)):
                return float(obj)
            elif isinstance(obj, pd.Timestamp):
                return obj.isoformat()
            elif isinstance(obj, (datetime.datetime, datetime.date)):
                return obj.isoformat()
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_numpy(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy(i) for i in obj]
            return obj

        return convert_numpy({
            "ticker": ticker,
            "chart_data": {
                "dates": df_features.index.strftime('%Y-%m-%d').tolist(),
                "actual_prices": data.loc[df_features.index]['Close'].tolist(),
                "predicted_prices": test_preds_real.tolist(),
                "future_dates": future_dates.strftime('%Y-%m-%d').tolist(),
                "future_prices": future_preds_real.tolist(),
            },
            "metrics": {
                "prediction_accuracy": rf_metrics.get("accuracy", 0),
                "model_confidence": final_confidence,
                "market_bias": "Bullish" if (data['Close'].iloc[-1] > data['Close'].iloc[-20]) else "Bearish",
                "volatility": df_features['Volatility'].iloc[-1]
            },
            "signal": {
                "label": final_conf_label,
                "confidence": final_confidence
            },
            "news": news_items,
            "fundamentals": fundamentals,
            "trade_setup": trade_setup
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/api/predict")
async def predict_endpoint(req: AnalysisRequest):
    return run_full_prediction_pipeline(req)

class DashboardRequest(BaseModel):
    request_id: Optional[str] = None

@app.post("/api/dashboard-metrics")
async def dashboard_metrics(req: DashboardRequest):
    # Use a default ticker like Nifty for general market metrics
    analysis_req = AnalysisRequest(ticker="^NSEI", fast_mode=True, request_id=req.request_id)
    try:
        # We only need the 'metrics' part of the result
        result = run_full_prediction_pipeline(analysis_req)
        return result.get("metrics", {})
    except HTTPException as e:
        # Fallback in case of error
        return {"prediction_accuracy": 0.0, "model_confidence": 0.0, "market_bias": "Neutral", "volatility": 0.0}

@app.get("/api/market-news")
async def market_news():
    return get_broad_market_news("Indian stock market")
    
if __name__ == "__main__":
    import argparse
    import sys

    # Check if arguments are provided
    if len(sys.argv) > 1:
        # Run hyperparameter tuning if arguments are provided
        parser = argparse.ArgumentParser(description="Hyperparameter Tuning for TFT Model")
        parser.add_argument(
            "--ticker",
            type=str,
            required=True,
            help="NSE ticker symbol to tune for (e.g., 'RELIANCE.NS')"
        )
        parser.add_argument(
            "--period",
            type=str,
            default="5y",
            help="Period for historical data (e.g., '1y', '5y')"
        )
        parser.add_argument(
            "--time_steps",
            type=int,
            default=60,
            help="Number of time steps for input sequences"
        )

        args = parser.parse_args()

        # Run the hyperparameter search with the provided ticker
        run_hyperparameter_search(ticker=args.ticker, period=args.period, time_steps=args.time_steps)
    else:
        # Run the FastAPI server if no arguments are provided
        uvicorn.run(app, host="0.0.0.0", port=8001)
