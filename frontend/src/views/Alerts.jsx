import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router';
import { getAlerts, markAlertRead, approveAlert } from '@medireview/api/client';
import { useAppPath } from '@medireview/lib/app-root.jsx';

const ALERT_LABELS = {
  complaint: '🟠 컴플레인 리뷰가 감지되었습니다',
  claim: '🔴 클레임 리뷰가 감지되었습니다',
  low_rating: '⚠️ 저평점 리뷰가 등록되었습니다',  // legacy
  automation_held: '🚫 자동 대응이 보류되었습니다 (키워드 감지)',
  approval_needed: '⏳ AI 댓글이 생성되었습니다 — 승인이 필요합니다',
};

export default function Alerts() {
  const navigate = useNavigate();
  const appPath = useAppPath();
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // all | unread | read
  const [approving, setApproving] = useState(null);

  const fetchAlerts = () =>
    getAlerts()
      .then((res) => setAlerts(res.data))
      .catch((err) => console.error('알림 조회 실패:', err))
      .finally(() => setLoading(false));

  useEffect(() => {
    fetchAlerts();
    const id = setInterval(fetchAlerts, 60000);
    return () => clearInterval(id);
  }, []);

  const handleRead = async (alertId) => {
    try {
      await markAlertRead(alertId);
      setAlerts((prev) =>
        prev.map((a) => (a.id === alertId ? { ...a, is_read: true } : a))
      );
    } catch (err) {
      console.error('읽음 처리 실패:', err);
    }
  };

  const handleApprove = async (e, alertId) => {
    e.stopPropagation();
    setApproving(alertId);
    try {
      await approveAlert(alertId);
      setAlerts((prev) =>
        prev.map((a) =>
          a.id === alertId ? { ...a, is_read: true, type: 'approved' } : a
        )
      );
    } catch (err) {
      alert(err.response?.data?.detail || '승인 실패');
    } finally {
      setApproving(null);
    }
  };

  const handleClick = (alert) => {
    if (!alert.is_read) handleRead(alert.id);
    navigate(appPath(`reviews/${alert.review_id}`));
  };

  const filtered = alerts.filter((a) => {
    if (filter === 'unread') return !a.is_read;
    if (filter === 'read') return a.is_read;
    return true;
  });

  const unreadCount = alerts.filter((a) => !a.is_read).length;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-800">
          알림
          {unreadCount > 0 && (
            <span className="ml-2 text-sm font-normal text-red-500">
              ({unreadCount}건 미확인)
            </span>
          )}
        </h2>

        {/* 필터 */}
        <div className="flex gap-2">
          {[
            { key: 'all', label: '전체' },
            { key: 'unread', label: '미확인' },
            { key: 'read', label: '확인됨' },
          ].map((f) => (
            <button
              key={f.key}
              onClick={() => setFilter(f.key)}
              className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                filter === f.key
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="text-center text-gray-400 py-12">불러오는 중...</div>
      ) : filtered.length === 0 ? (
        <div className="text-center text-gray-400 py-12">
          {filter === 'unread' ? '미확인 알림이 없습니다.' : '알림이 없습니다.'}
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((a) => (
            <div
              key={a.id}
              onClick={() => handleClick(a)}
              className={`p-4 rounded-lg border cursor-pointer transition-all hover:shadow-md ${
                a.is_read
                  ? 'bg-white border-gray-200'
                  : a.type === 'approval_needed'
                    ? 'bg-yellow-50 border-yellow-200'
                    : a.type === 'complaint'
                      ? 'bg-orange-50 border-orange-200'
                      : 'bg-red-50 border-red-200'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {!a.is_read && (
                    <span className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${
                      a.type === 'approval_needed' ? 'bg-yellow-500'
                        : a.type === 'complaint' ? 'bg-orange-500'
                        : 'bg-red-500'
                    }`} />
                  )}
                  <div>
                    <p className={`text-sm font-medium ${a.is_read ? 'text-gray-600' : 'text-gray-800'}`}>
                      {a.type === 'approved'
                        ? '✅ 승인 완료 — 댓글이 등록되었습니다'
                        : ALERT_LABELS[a.type] || '알림'}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">
                      리뷰 #{a.review_id} · {new Date(a.created_at).toLocaleString('ko-KR')}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {a.type === 'approval_needed' && !a.is_read && (
                    <button
                      onClick={(e) => handleApprove(e, a.id)}
                      disabled={approving === a.id}
                      className="px-3 py-1.5 text-xs font-medium bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                    >
                      {approving === a.id ? '처리중...' : '승인'}
                    </button>
                  )}
                  <span className="text-xs text-indigo-500 hover:text-indigo-700">
                    리뷰 보기 →
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
