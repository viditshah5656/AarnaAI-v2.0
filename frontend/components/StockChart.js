'use client';

import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const StockChart = ({ data }) => {

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { display: false },
        tooltip: {
            mode: 'index',
            intersect: false,
            backgroundColor: 'rgba(0,0,0,0.7)',
            titleFont: { size: 16, weight: 'bold' },
            bodyFont: { size: 14 },
            padding: 12,
            caretSize: 10,
            cornerRadius: 8,
            displayColors: false,
        },
    },
    scales: {
        x: {
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { display: false },
        },
        y: {
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { 
                callback: (value) => `$${value}`,
                color: '#a0a0a0',
             },
        },
    },
  };

  const chartData = {
    labels: data.labels,
    datasets: [
      {
        label: 'Price',
        data: data.prices,
        borderColor: '#007BFF',
        backgroundColor: 'rgba(0, 123, 255, 0.5)',
        borderWidth: 3,
        pointRadius: 0,
        tension: 0.4,
        fill: true,
      },
    ],
  };

  return <div className="h-96 w-full"> <Line options={options} data={chartData} /></div>;
};

export default StockChart;
