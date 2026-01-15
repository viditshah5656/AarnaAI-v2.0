export const fetchStockData = async (ticker) => {
    try {
      const response = await fetch(`http://localhost:8001/api/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ticker }),
      });
  
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
  
      const data = await response.json();
      return {
        labels: data.dates,
        prices: data.actual_prices,
      };
    } catch (error) {
      console.error("Error fetching stock data:", error);
      // Return empty data in case of an error
      return { labels: [], prices: [] };
    }
  };
  