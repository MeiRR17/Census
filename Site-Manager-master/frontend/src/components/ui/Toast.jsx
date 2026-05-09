import { useEffect } from 'react';
import { CheckCircle, AlertCircle, XCircle, Info } from 'lucide-react';

const icons = {
  success: CheckCircle,
  error: XCircle,
  warning: AlertCircle,
  info: Info,
};

const colors = {
  success: 'bg-gray-900 border-gray-700 text-green-400',
  error: 'bg-red-900 border-red-700 text-red-400',
  warning: 'bg-amber-900 border-amber-700 text-amber-400',
  info: 'bg-blue-900 border-blue-700 text-blue-400',
};

/**
 * Toast notification component
 * @param {Object} props
 * @param {string} props.msg - Message to display
 * @param {string} props.type - 'success' | 'error' | 'warning' | 'info'
 * @param {number} props.duration - Duration in ms (default: 3000)
 * @param {Function} props.onClose - Callback when toast closes
 */
export const Toast = ({ msg, type = 'success', duration = 3000, onClose }) => {
  const Icon = icons[type];

  useEffect(() => {
    if (!msg) return;
    const timer = setTimeout(() => {
      onClose?.();
    }, duration);
    return () => clearTimeout(timer);
  }, [msg, duration, onClose]);

  if (!msg) return null;

  return (
    <div
      className={`fixed top-6 right-6 z-50 flex items-center gap-3 px-5 py-3.5 rounded-2xl shadow-2xl border animate-fade-in ${colors[type]}`}
    >
      <Icon size={18} className="shrink-0" />
      <span className="text-sm font-medium text-white">{msg}</span>
    </div>
  );
};

export default Toast;
