const TopMovers = ({ movers }) => {
  return (
    <div className="bg-white/10 backdrop-blur-sm border border-white/20 p-6 rounded-lg shadow-lg">
      <h2 className="text-xl font-semibold mb-4 text-text-primary">Top Movers</h2>
      <table className="w-full">
        <thead>
          <tr className="text-left text-text-secondary">
            <th className="pb-2">Ticker</th>
            <th className="pb-2">Price</th>
            <th className="pb-2">Change</th>
          </tr>
        </thead>
        <tbody>
          {movers && movers.length > 0 ? (
            movers.map((mover, index) => (
              <tr key={index} className="border-t border-white/20">
                <td className="py-2">{mover.ticker}</td>
                <td className="py-2">{mover.price}</td>
                <td className={`py-2 ${mover.isUp ? 'text-green-500' : 'text-red-500'}`}>{mover.change}</td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan="3" className="py-2 text-center text-text-secondary">Top movers will appear here.</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
};

export default TopMovers;
