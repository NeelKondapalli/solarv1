import React from 'react';
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
import { Line } from 'react-chartjs-2';

// Register ChartJS components
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

export function CoinChart({ data, title }) {
  const chartData = {
    labels: data.timestamps,
    datasets: [
      {
        label: title,
        data: data.prices,
        borderColor: 'rgb(219, 39, 119)', // pink-600
        backgroundColor: 'rgba(219, 39, 119, 0.1)',
        fill: true,
        tension: 0.4,
        pointRadius: 2,
        pointHoverRadius: 5,
        pointBackgroundColor: 'rgb(219, 39, 119)',
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    plugins: {
      legend: {
        position: 'top',
        labels: {
          font: {
            family: 'system-ui',
            size: 12,
          },
          boxWidth: 4,
          usePointStyle: true,
        },
      },
      title: {
        display: false,
      },
      tooltip: {
        backgroundColor: 'white',
        titleColor: 'rgb(17, 24, 39)',
        bodyColor: 'rgb(17, 24, 39)',
        bodyFont: {
          family: 'system-ui',
        },
        borderColor: 'rgb(229, 231, 235)',
        borderWidth: 1,
        padding: 12,
        boxWidth: 8,
        boxHeight: 8,
        usePointStyle: true,
        callbacks: {
          label: function(context) {
            return `${context.dataset.label}: $${context.parsed.y.toFixed(2)}`;
          }
        }
      },
    },
    scales: {
      x: {
        grid: {
          display: false,
        },
        ticks: {
          font: {
            family: 'system-ui',
            size: 11,
          },
          maxRotation: 0,
        },
      },
      y: {
        grid: {
          color: 'rgb(243, 244, 246)',
        },
        ticks: {
          font: {
            family: 'system-ui',
            size: 11,
          },
          callback: function(value) {
            return '$' + value.toFixed(2);
          },
        },
      },
    },
  };

  return (
    <div className="w-full h-[300px] bg-white rounded-lg p-4 border border-gray-200">
      <Line data={chartData} options={options} />
    </div>
  );
} 