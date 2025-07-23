// src/App.jsx
import { useState, useEffect } from 'react';
import { supabase } from './supabaseClient';
import { Radar } from 'react-chartjs-2';
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

  // Form state - replaced with natural language input
  const [searchQuery, setSearchQuery] = useState('');

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

    // Send natural language query to backend
    try {
        const response = await fetch('https://hexar-backend.onrender.com/api/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ search_query: searchQuery }),
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
          <div className="max-w-4xl mx-auto bg-gray-900 p-8 rounded-lg shadow-lg">
            <form onSubmit={handleSubmit}>
              <div className="mb-6">
                <label className="block mb-4 text-lg font-bold text-center">What gear are you looking for?</label>
                <div className="relative">
                  <textarea
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Tell us what you need! For example: 'I'm looking for an intermediate all-mountain snowboard under $400' or 'Need beginner-friendly boots for freestyle riding'"
                    className="w-full p-4 bg-gray-800 rounded-lg border border-gray-700 text-white placeholder-gray-400 resize-none h-24 focus:ring-2 focus:ring-white focus:border-transparent"
                    required
                  />
                  <div className="absolute bottom-2 right-2 text-xs text-gray-500">
                    {searchQuery.length}/200
                  </div>
                </div>
                <div className="mt-2 text-sm text-gray-400">
                  💡 Try including: product type, skill level, riding style, budget, or specific features you want
                </div>
              </div>
              <button 
                type="submit" 
                className="w-full bg-white text-black font-bold py-4 px-6 rounded-lg hover:bg-gray-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed" 
                disabled={isLoading || !searchQuery.trim()}
              >
                {isLoading ? (
                  <span className="flex items-center justify-center">
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-black" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    AI is researching your perfect gear...
                  </span>
                ) : (
                  'Find My Perfect Gear'
                )}
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
    const [bookmarkedItems, setBookmarkedItems] = useState(new Set());
    
    const toggleBookmark = (productId) => {
        setBookmarkedItems(prev => {
            const newSet = new Set(prev);
            if (newSet.has(productId)) {
                newSet.delete(productId);
            } else {
                newSet.add(productId);
            }
            return newSet;
        });
    };

    if (!results || !results.products) return null;
    
    return (
        <div className="mt-12">
            <h2 className="text-3xl font-bold text-center mb-8">Perfect Matches for You</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {results.products.map((item, index) => (
                    <div key={index} className="bg-gray-900 p-6 rounded-lg flex flex-col relative">
                        {/* Bookmark Button */}
                        <button
                            onClick={() => toggleBookmark(index)}
                            className="absolute top-4 right-4 z-10 p-2 rounded-full bg-black bg-opacity-50 hover:bg-opacity-70 transition-colors"
                        >
                            <svg
                                className={`w-6 h-6 ${bookmarkedItems.has(index) ? 'text-yellow-400 fill-current' : 'text-white'}`}
                                fill={bookmarkedItems.has(index) ? 'currentColor' : 'none'}
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                            >
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                            </svg>
                        </button>

                        <img src={item.image_url} alt={item.name} className="w-full h-48 object-cover rounded mb-4" />
                        <h3 className="text-xl font-bold mb-2">{item.name}</h3>
                        <div className="flex justify-between items-center mb-4">
                            <p className="text-2xl font-bold text-green-400">{item.price}</p>
                            <div className="flex items-center">
                                <span className="text-yellow-400 text-lg">★</span>
                                <span className="text-white font-bold ml-1">{item.overall_rating}/10</span>
                            </div>
                        </div>
                        
                        <div className="w-full h-64 mb-4"><HexarChart ratings={item.ratings} /></div>

                        <div className="text-sm mb-4 flex-grow">
                            <h4 className="font-bold text-green-400 mb-1">✓ Pros</h4>
                            <ul className="list-none text-gray-300 mb-3">
                                {item.pros.map((pro, i) => <li key={i} className="mb-1">• {pro}</li>)}
                            </ul>
                            <h4 className="font-bold text-red-400 mb-1">✗ Cons</h4>
                            <ul className="list-none text-gray-300">
                                {item.cons.map((con, i) => <li key={i} className="mb-1">• {con}</li>)}
                            </ul>
                        </div>

                        <a 
                            href={item.retailer_url} 
                            target="_blank" 
                            rel="noopener noreferrer" 
                            className="mt-auto block text-center w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white font-bold py-3 px-4 rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all transform hover:scale-105"
                        >
                            Shop Now - Best Deal 🔗
                        </a>
                    </div>
                ))}
            </div>
        </div>
    );
}