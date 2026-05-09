import { useState } from 'react';
import { Plus, RefreshCw } from 'lucide-react';

/**
 * Reusable Page Header component
 * @param {Object} props
 * @param {string} props.title - Page title
 * @param {string} props.subtitle - Page subtitle/description
 * @param {Function} props.onRefresh - Callback for refresh button
 * @param {Function} props.onAdd - Callback for add button
 * @param {string} props.addLabel - Label for add button
 * @param {boolean} props.canAdd - Whether to show add button
 * @param {React.ReactNode} props.extraActions - Additional action buttons
 */
export const PageHeader = ({
  title,
  subtitle,
  onRefresh,
  onAdd,
  addLabel = 'הוסף',
  canAdd = true,
  extraActions,
}) => {
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = async () => {
    if (!onRefresh || isRefreshing) return;
    setIsRefreshing(true);
    try {
      await onRefresh();
    } finally {
      setIsRefreshing(false);
    }
  };

  return (
    <div className="flex items-center justify-between">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
        {subtitle && <p className="text-sm text-gray-500 mt-1">{subtitle}</p>}
      </div>
      <div className="flex items-center gap-3">
        {onRefresh && (
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-xl hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw size={16} className={`text-gray-600 ${isRefreshing ? 'animate-spin' : ''}`} />
            <span className="text-sm text-gray-700">{isRefreshing ? 'טוען...' : 'רענן'}</span>
          </button>
        )}
        {extraActions}
        {canAdd && onAdd && (
          <button
            onClick={onAdd}
            className="flex items-center gap-2 bg-indigo-600 text-white px-5 py-2.5 rounded-xl font-medium hover:bg-indigo-700 transition-all shadow-sm"
          >
            <Plus size={18} />
            {addLabel}
          </button>
        )}
      </div>
    </div>
  );
};

export default PageHeader;
