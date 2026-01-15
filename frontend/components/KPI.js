const KPI = ({ title, value }) => {
  return (
    <div className="bg-white/10 backdrop-blur-sm border border-white/20 p-6 rounded-lg shadow-lg">
      <h3 className="text-sm font-medium text-text-secondary mb-2">{title}</h3>
      <p className="text-3xl font-semibold text-text-primary">{value}</p>
    </div>
  );
};

export default KPI;
