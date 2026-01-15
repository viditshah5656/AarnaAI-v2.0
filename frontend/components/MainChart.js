'use client';

import Plot from 'react-plotly.js';

const MainChart = ({ data }) => {
  if (!data) {
    return (
      <div className="bg-card p-6 rounded-lg shadow-md h-full flex items-center justify-center">
        <p className="text-text-secondary">Search for a stock to see its chart.</p>
      </div>
    );
  }

  const plotData = [
    {
      x: data.dates,
      y: data.actual_prices,
      type: 'scatter',
      mode: 'lines',
      name: 'Actual Price',
      line: { color: '#4f46e5' },
    },
  ];

  if (data.predicted_prices) {
    plotData.push({
      x: data.dates.slice(data.dates.length - data.predicted_prices.length),
      y: data.predicted_prices,
      type: 'scatter',
      mode: 'lines',
      name: 'Predicted Price',
      line: { color: '#f59e0b', dash: 'dot' },
    });
  }

  return (
    <div className="bg-card p-6 rounded-lg shadow-md h-full">
      <Plot
        data={plotData}
        layout={{
          autosize: true,
          title: `Stock Price Analysis for ${data.ticker}`,
          paper_bgcolor: '#252525',
          plot_bgcolor: '#252525',
          font: { color: '#ffffff' },
          xaxis: { 
            gridcolor: '#3f3f46',
            rangeslider: {visible: false}
          },
          yaxis: { gridcolor: '#3f3f46' },
          legend: {orientation: 'h', y: -0.2}
        }}
        useResizeHandler={true}
        style={{ width: '100%', height: '100%' }}
      />
    </div>
  );
};

export default MainChart;
