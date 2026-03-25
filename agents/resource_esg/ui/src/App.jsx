import { useState, useEffect } from 'react';
import axios from 'axios';
import {
  PieChart, Pie, Cell, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const COLORS = { LOW: '#22c55e', MEDIUM: '#eab308', HIGH: '#f97316', CRITICAL: '#ef4444' };
const RESOURCE_COLORS = ['#3b82f6', '#8b5cf6', '#f59e0b'];

export default function App() {
  const [shipments, setShipments] = useState([]);
  const [riskData, setRiskData] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      setLoading(true);
      const res = await axios.get(`${API_URL}/api/v1/esg/resource/all/shipments`);
      setShipments(res.data || []);

      // Aggregate risk by resource_type
      const counts = {};
      (res.data || []).forEach(s => {
        const rt = s.resource_type || 'unknown';
        counts[rt] = (counts[rt] || 0) + 1;
      });
      setRiskData(Object.entries(counts).map(([name, value]) => ({ name, value })));
    } catch (e) {
      console.error('API error:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const filtered = filter === 'all' ? shipments : shipments.filter(s => s.resource_type === filter);

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-green-400">ResourceESGAgent Dashboard</h1>
        <p className="text-gray-400 mt-1">Real-time ESG risk monitoring: timber / amber / ore</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="bg-gray-800 rounded-xl p-4">
          <h2 className="text-lg font-semibold mb-4">Shipments by Resource Type</h2>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={riskData} cx="50%" cy="50%" outerRadius={80} dataKey="value" label>
                {riskData.map((_, i) => <Cell key={i} fill={RESOURCE_COLORS[i % RESOURCE_COLORS.length]} />)}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-gray-800 rounded-xl p-4">
          <h2 className="text-lg font-semibold mb-4">Volume by Resource</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={riskData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="name" stroke="#9ca3af" />
              <YAxis stroke="#9ca3af" />
              <Tooltip />
              <Bar dataKey="value" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-gray-800 rounded-xl p-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Shipments</h2>
          <select
            className="bg-gray-700 border border-gray-600 rounded px-3 py-1 text-sm"
            value={filter} onChange={e => setFilter(e.target.value)}
          >
            <option value="all">All resources</option>
            <option value="timber">Timber</option>
            <option value="amber">Amber</option>
            <option value="ore">Ore</option>
          </select>
        </div>
        {loading ? <p className="text-gray-400">Loading...</p> : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-400 border-b border-gray-700">
                <th className="text-left py-2">Enterprise</th>
                <th className="text-left py-2">Resource</th>
                <th className="text-left py-2">Category</th>
                <th className="text-right py-2">Volume m3</th>
                <th className="text-right py-2">Risk</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((s, i) => (
                <tr key={i} className="border-b border-gray-700 hover:bg-gray-750">
                  <td className="py-2">{s.enterprise_id}</td>
                  <td className="py-2">{s.resource_type}</td>
                  <td className="py-2">{s.declared_category}</td>
                  <td className="py-2 text-right">{s.volume_m3}</td>
                  <td className="py-2 text-right">
                    <span className="px-2 py-0.5 rounded text-xs font-bold"
                      style={{ backgroundColor: COLORS[s.risk_level] || '#6b7280' }}>
                      {s.risk_level || 'N/A'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
