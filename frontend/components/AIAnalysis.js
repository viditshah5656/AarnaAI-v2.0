import { marked } from 'marked';

const AIAnalysis = ({ content }) => {
  const renderContent = () => {
    if (!content) {
      return <p className="text-text-secondary">AI analysis will appear here after you search for a stock.</p>;
    }
    const htmlContent = marked(content);
    return <div dangerouslySetInnerHTML={{ __html: htmlContent }} />;
  };

  return (
    <div className="bg-card p-6 rounded-lg shadow-md h-full prose prose-invert max-w-none">
      <h2 className="text-xl font-semibold mb-4 text-text-primary">AI Analysis & Report</h2>
      {renderContent()}
    </div>
  );
};

export default AIAnalysis;
