import { useEffect, useState } from 'react';
import { Layers, Plus, UserPlus, RefreshCw } from 'lucide-react';
import api from '../api.js';
import { useAuth } from '../context/AuthContext.jsx';
import { Toast, Modal, PageHeader, LoadingSkeleton } from '../components/ui/index.js';

const Groups = () => {
  const { isSuperAdmin } = useAuth();
  const [groups,  setGroups]  = useState([]);
  const [users,   setUsers]   = useState([]);
  const [loading, setLoading] = useState(true);
  const [modal,   setModal]   = useState(false);
  const [addUser, setAddUser] = useState(null); // group_id
  const [form,    setForm]    = useState({ name: '', description: '', classification: 'viewer' });
  const [addForm, setAddForm] = useState({ user_id: '' });
  const [error,   setError]   = useState('');
  const [toast,   setToast]   = useState('');

  const showToast = (msg) => setToast(msg);
  const hideToast = () => setToast('');

  const fetchAll = async () => {
    try {
      const [gr, us] = await Promise.all([
        api.get('/api/v1/groups/'),
        api.get('/api/v1/users/'),
      ]);
      setGroups(gr.data);
      setUsers(us.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAll(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault(); setError('');
    try {
      await api.post('/api/v1/groups/', form);
      setModal(false);
      setForm({ name: '', description: '', classification: 'viewer' });
      await fetchAll(); // ← מרענן אחרי יצירה
      showToast(`✅ Group "${form.name}" נוצר בהצלחה`);
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to create group');
    }
  };

  const handleAddUser = async (e) => {
    e.preventDefault(); setError('');
    const groupName = groups.find(g => g.id === addUser)?.name || '';
    const userName  = users.find(u => u.id === addForm.user_id)?.username || '';
    try {
      await api.post(`/api/v1/groups/${addUser}/add-user`, null, {
        params: { user_id: addForm.user_id }
      });
      setAddUser(null);
      setAddForm({ user_id: '' });
      await fetchAll(); // ← תוקן: מרענן אחרי הוספת משתמש
      showToast(`✅ ${userName} נוסף ל-${groupName}`);
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to add user');
    }
  };

  // Loading Skeleton
  if (loading) {
    return <LoadingSkeleton type="page" count={3} />;
  }

  return (
    <div className="space-y-6">
      <Toast msg={toast} onClose={hideToast} />

      <PageHeader
        title="Groups"
        subtitle="ניהול קבוצות גישה וחברים"
        onRefresh={fetchAll}
        onAdd={() => { setModal(true); setError(''); }}
        addLabel="קבוצה חדשה"
      />

      {/* רשימת קבוצות */}
      <div className="grid gap-4">
        {groups.map(g => (
          <div key={g.id} className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-cyan-50 rounded-lg">
                  <Layers size={18} className="text-cyan-600" />
                </div>
                <div>
                  <p className="font-semibold text-gray-900">{g.name}</p>
                  {g.description && <p className="text-xs text-gray-400 mt-0.5">{g.description}</p>}
                  <p className="text-xs text-gray-400 mt-1">
                    נוצר: {new Date(g.created_at).toLocaleDateString('he-IL')}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs bg-gray-100 text-gray-500 px-2.5 py-1 rounded-full font-medium uppercase tracking-wide">
                  {g.classification}
                </span>
                <button
                  onClick={() => { setAddUser(g.id); setAddForm({ user_id: '' }); setError(''); }}
                  className="p-1.5 rounded-lg hover:bg-indigo-50 text-gray-400 hover:text-indigo-600 transition-colors"
                  title="הוסף משתמש">
                  <UserPlus size={16} />
                </button>
              </div>
            </div>
          </div>
        ))}
        {groups.length === 0 && (
          <div className="bg-white rounded-2xl border border-gray-100 p-12 text-center">
            <Layers size={40} className="mx-auto text-gray-200 mb-3" />
            <p className="text-gray-400">אין קבוצות עדיין.</p>
          </div>
        )}
      </div>

      {/* Modal: יצירת קבוצה */}
      <Modal
        isOpen={modal}
        onClose={() => { setModal(false); setError(''); }}
        title="יצירת קבוצה חדשה"
        size="sm"
      >
        <form onSubmit={handleCreate} className="space-y-4">
          <input placeholder="שם הקבוצה" required
            className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-sm"
            value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} />
          <input placeholder="תיאור (אופציונלי)"
            className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-sm"
            value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} />
          <select
            className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-sm bg-white"
            value={form.classification} onChange={e => setForm({ ...form, classification: e.target.value })}>
            <option value="viewer">Viewer</option>
            <option value="operator">Operator</option>
            <option value="admin">Admin</option>
          </select>
          {error && <p className="text-sm text-red-500">{error}</p>}
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={() => { setModal(false); setError(''); }}
              className="flex-1 px-4 py-3 text-gray-600 hover:bg-gray-50 rounded-xl text-sm">ביטול</button>
            <button type="submit"
              className="flex-1 px-4 py-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 text-sm">צור קבוצה</button>
          </div>
        </form>
      </Modal>

      {/* Modal: הוספת משתמש לקבוצה */}
      <Modal
        isOpen={!!addUser}
        onClose={() => { setAddUser(null); setError(''); }}
        title="הוספת משתמש לקבוצה"
        size="sm"
      >
        <p className="text-sm text-gray-500 mb-4">
          קבוצה: <span className="font-medium text-indigo-600">{groups.find(g => g.id === addUser)?.name}</span>
        </p>
        <form onSubmit={handleAddUser} className="space-y-4">
          <select
            className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none text-sm bg-white"
            value={addForm.user_id}
            onChange={e => setAddForm({ user_id: e.target.value })}
            required>
            <option value="">בחר משתמש</option>
            {users
              .filter(u => u.role !== 'superadmin')
              .map(u => (
                <option key={u.id} value={u.id}>
                  {u.username} ({u.role})
                </option>
              ))
            }
          </select>
          {error && <p className="text-sm text-red-500">{error}</p>}
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={() => { setAddUser(null); setError(''); }}
              className="flex-1 px-4 py-3 text-gray-600 hover:bg-gray-50 rounded-xl text-sm">ביטול</button>
            <button type="submit"
              className="flex-1 px-4 py-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 text-sm">הוסף</button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default Groups;