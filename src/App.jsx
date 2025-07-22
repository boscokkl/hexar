// src/App.jsx
import { useState, useEffect } from 'react';
import { supabase } from './supabaseClient';
import { Bar, Radar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend
);

// --- Static Data for Masked Preview ---
const MASKED_PREVIEW_DATA = {
    products: [
        { name: "Brand A 'Dream' Board", image_url: "https://via.placeholder.com/300x300.png/000000?text=Board+A", retailer_url: "#", price: "$XXX", pros: ["Great for beginners", "Durable build"], cons: ["Not for experts"], ratings: { Price: 8, Level: 9, Quality: 7, Performance: 6, Versatility: 8, Style: 7 }, overall_rating: 7.5 },
        { name: "Brand B 'Pro' Board", image_url: "https://via.placeholder.com/300x300.png/000000?text=Board+B", retailer_url: "#", price: "$XXX", pros: ["Excellent performance", "Lightweight"], cons: ["Expensive"], ratings: { Price: 4, Level: 7, Quality: 9, Performance: 9, Versatility: 6, Style: 8 }, overall_rating: 8.1 },
        { name: "Brand C 'All-Mtn' Board", image_url: "https://via.placeholder.com/300x300.png/000000?text=Board+C", retailer_url: "#", price: "$XXX", pros: ["Super versatile", "Good value"], cons: ["Average style"], ratings: { Price: 7, Level: 8, Quality: 8, Performance: 7, Versatility: 9, Style: 6 }, overall_rating: 7.8 },
    ]
};

// --- Chart Component ---
const HexarChart = ({ ratings }) => {
  const data = {
    labels: ['Price', 'Level', 'Quality', 'Performance', 'Versatility', 'Style'],
    datasets: [
      {
        label: 'Rating',
        data: Object.values(ratings),
        backgroundColor: 'rgba(255, 255, 255, 0.2)',
        borderColor: 'rgba(255, 255, 255, 1)',
        borderWidth: 1,
      },
    ],
  };
  const options = {
    scales: {
      r: {
        angleLines: { color: 'rgba(255, 255, 255, 0.2)' },
        grid: { color: 'rgba(255, 255, 255, 0.2)' },
        pointLabels: { color: 'white', font: { size: 14 } },
        suggestedMin: 0,
        suggestedMax: 10,
        ticks: { display: false }
      },
    },
    plugins: { legend: { display: false } },
  };
  return <Radar data={data} options={options} />;
};

// --- Main App Component ---
export default function App() {
  const [session, setSession] = useState(null);
  const [results, setResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showMasked, setShowMasked] = useState(false);
  const [error, setError] = useState('');

  // Form state
  const [level, setLevel] = useState('intermediate');
  const [style, setStyle] = useState('all-mountain');
  const [productType, setProductType] = useState('snowboard');

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => setSession(session));
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => setSession(session));
    return () => subscription.unsubscribe();
  }, []);

  const handleLogin = async (e) => {
    e.preventDefault();
    const email = e.target.email.value;
    try {
        await supabase.auth.signInWithOtp({ email });
        alert('Check your email for the login link!');
    } catch (error) {
        alert(error.error_description || error.message);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!session) {
        setResults(MASKED_PREVIEW_DATA);
        setShowMasked(true);
        return;
    }

    setIsLoading(true);
    setShowMasked(false);
    setResults(null);

    // This is where you would call your backend API
    // For local development, make sure your Python backend is running
    try {
        const response = await fetch('http://127.0.0.1:8000/api/query', { // Replace with your deployed backend URL later
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ level, style, product_type: productType }),
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Failed to fetch results');
        }
        const data = await response.json();
        setResults(data);
    } catch (err) {
        setError(err.message);
    } finally {
        setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black text-white font-sans">
      <div className="container mx-auto p-4 md:p-8">
        <header className="text-center mb-12">
          <h1 className="text-5xl font-bold mb-2">Hexar</h1>
          <p className="text-xl text-gray-400">Gear Up! Your AI-Powered Product Comparator.</p>
        </header>

        <main>
          <div className="max-w-2xl mx-auto bg-gray-900 p-8 rounded-lg shadow-lg">
            <form onSubmit={handleSubmit}>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div>
                  <label className="block mb-2 text-sm font-bold">Product Type</label>
                  <select value={productType} onChange={(e) => setProductType(e.target.value)} className="w-full p-2 bg-gray-800 rounded border border-gray-700">
                    <option value="snowboard">Snowboard</option>
                    <option value="boots">Boots</option>
                    <option value="bindings">Bindings</option>
                  </select>
                </div>
                <div>
                  <label className="block mb-2 text-sm font-bold">Your Level</label>
                  <select value={level} onChange={(e) => setLevel(e.target.value)} className="w-full p-2 bg-gray-800 rounded border border-gray-700">
                    <option value="beginner">Beginner</option>
                    <option value="intermediate">Intermediate</option>
                    <option value="advanced">Advanced</option>
                  </select>
                </div>
                <div>
                  <label className="block mb-2 text-sm font-bold">Riding Style</label>
                  <select value={style} onChange={(e) => setStyle(e.target.value)} className="w-full p-2 bg-gray-800 rounded border border-gray-700">
                    <option value="all-mountain">All-Mountain</option>
                    <option value="freestyle">Freestyle</option>
                    <option value="freeride">Freeride</option>
                  </select>
                </div>
              </div>
              <button type="submit" className="w-full bg-white text-black font-bold py-3 px-4 rounded hover:bg-gray-300 transition-colors" disabled={isLoading}>
                {isLoading ? 'Researching...' : 'Get Comparison'}
              </button>
            </form>
          </div>

          {error && <div className="text-center text-red-500 mt-4">{error}</div>}

          {showMasked && !session && (
              <div className="text-center mt-8 p-6 bg-gray-900 rounded-lg relative">
                  <div className="absolute inset-0 bg-black bg-opacity-50 backdrop-blur-sm flex items-center justify-center z-10">
                      <div className="text-center">
                          <h3 className="text-2xl font-bold">Unlock Your Personalized Results</h3>
                          <p className="text-gray-400 mb-4">Sign in to see your live product comparison.</p>
                          <form onSubmit={handleLogin} className="flex flex-col gap-2 max-w-sm mx-auto">
                            <input name="email" type="email" placeholder="your@email.com" required className="p-2 bg-gray-800 rounded border border-gray-700 text-center"/>
                            <button type="submit" className="bg-white text-black font-bold py-2 px-4 rounded">Send Login Link</button>
                          </form>
                      </div>
                  </div>
                  <ResultsDisplay results={results} />
              </div>
          )}

          {isLoading && <div className="text-center mt-8">⚙️ Finding the best gear for you...</div>}

          {results && !showMasked && session && <ResultsDisplay results={results} />}

        </main>
      </div>
    </div>
  );
}

// --- Results Display Component ---
const ResultsDisplay = ({ results }) => {
    if (!results || !results.products) return null;
    return (
        <div className="mt-12">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {results.products.map((item, index) => (
                    <div key={index} className="bg-gray-900 p-6 rounded-lg flex flex-col">
                        <img src={item.image_url} alt={item.name} className="w-full h-48 object-cover rounded mb-4" />
                        <h3 className="text-xl font-bold mb-2">{item.name}</h3>
                        <p className="text-2xl font-bold mb-4">{item.price}</p>
                        <div className="w-full h-64 mb-4"><HexarChart ratings={item.ratings} /></div>

                        <div className="text-sm mb-4 flex-grow">
                            <h4 className="font-bold text-green-400">Pros</h4>
                            <ul className="list-disc list-inside text-gray-300">
                                {item.pros.map((pro, i) => <li key={i}>{pro}</li>)}
                            </ul>
                            <h4 className="font-bold text-red-400 mt-2">Cons</h4>
                            <ul className="list-disc list-inside text-gray-300">
                                {item.cons.map((con, i) => <li key={i}>{con}</li>)}
                            </ul>
                        </div>

                        <a href={item.retailer_url} target="_blank" rel="noopener noreferrer" className="mt-auto block text-center w-full bg-white text-black font-bold py-2 px-4 rounded hover:bg-gray-300 transition-colors">
                            View Deal
                        </a>
                    </div>
                ))}
            </div>
        </div>
    );
}