import { AlertTriangle, Trash2 } from 'lucide-react';
import { Modal } from './Modal.jsx';

/**
 * Confirm Dialog component for destructive actions
 * @param {Object} props
 * @param {boolean} props.isOpen - Whether dialog is visible
 * @param {Function} props.onClose - Callback to close dialog
 * @param {Function} props.onConfirm - Callback when confirmed
 * @param {string} props.title - Dialog title
 * @param {string} props.message - Dialog message
 * @param {string} props.confirmText - Text for confirm button
 * @param {string} props.cancelText - Text for cancel button
 * @param {boolean} props.isDanger - Whether this is a dangerous action (red styling)
 */
export const ConfirmDialog = ({
  isOpen,
  onClose,
  onConfirm,
  title = 'אשר פעולה',
  message = 'האם אתה בטוח שברצונך לבצע פעולה זו?',
  confirmText = 'אשר',
  cancelText = 'בטל',
  isDanger = true,
}) => {
  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title} size="sm">
      <div className="space-y-6">
        <div className="flex items-start gap-4">
          <div
            className={`p-3 rounded-xl ${
              isDanger ? 'bg-red-50 text-red-500' : 'bg-amber-50 text-amber-500'
            }`}
          >
            {isDanger ? <Trash2 size={24} /> : <AlertTriangle size={24} />}
          </div>
          <p className="text-gray-600 mt-1">{message}</p>
        </div>

        <div className="flex gap-3 justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2.5 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-xl transition-colors"
          >
            {cancelText}
          </button>
          <button
            onClick={() => {
              onConfirm();
              onClose();
            }}
            className={`px-4 py-2.5 text-sm font-medium text-white rounded-xl transition-colors ${
              isDanger
                ? 'bg-red-600 hover:bg-red-700'
                : 'bg-indigo-600 hover:bg-indigo-700'
            }`}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </Modal>
  );
};

export default ConfirmDialog;
