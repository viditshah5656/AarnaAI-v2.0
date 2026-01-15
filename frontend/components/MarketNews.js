const MarketNews = ({ articles }) => {
  return (
    <div className="bg-card p-6 rounded-lg shadow-md">
      <h2 className="text-xl font-semibold mb-4 text-text-primary">Market News</h2>
      <div className="space-y-4">
        {articles && articles.length > 0 ? (
          articles.map((item, index) => (
            <div key={index}>
              <a href={item.link} target="_blank" rel="noopener noreferrer" className="text-text-primary hover:text-accent transition-colors">{item.title}</a>
              <p className="text-sm text-text-secondary">{item.source}</p>
            </div>
          ))
        ) : (
          <p className="text-text-secondary">News articles will appear here.</p>
        )}
      </div>
    </div>
  );
};

export default MarketNews;
