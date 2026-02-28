import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAlerts, markAlertRead } from '../api/client';
import StarRating from '../components/StarRating';
import PlatformBadge from '../components/PlatformBadge';

export default function Alerts() {
  const navigate = useNavigate();
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // all | unread | read

  useEffect(() => {
    fetchAlerts();
  }, []);

  const fetchAlerts = async () => {
    setLoading(true);
    try {
      const res = await getAlerts();
      setAlerts(res.data);
    } catch (err) {
      console.error('알림 조회 실패:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleClick = async (alert) => {
    // 읽음 처리
    if (!alert.is_read) {
      try {
        await markAlertRead(alert.id);
        setAlerts((prev) =>
          prev.map((a) => (a.id === alert.id ? { ...a, is_read: true } : a))
        );
      } catch (err) {
        console.error('읽음 처리 실패:', err);
      }
    }
    // 리뷰 상세로 이동
    navigate(`/reviews/${alert.review_id}`);
  };

  const filteredAlerts = alerts.filter((a) => {
    if (filter === 'unread') return !a.is_read;
    if (filter === 'read') return a.is_read;
    return true;
  });

  const unreadCount = alerts.filter((a) => !a.is_read).length;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <h2 className="text-2xl font-bold text-gray-800">알림</h2>
          {unreadCount > 0 && (
            <span className="inline-flex items-center justify-center px-2.5 py-0.5 text-xs font-bold text-white bg-red-500 rounded-full">
              {unreadCount}건
            </span>
          )}
        </div>

        {/* 필터 탭 */}
        <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
          {[
            { key: 'all', label: '전체' },
            { key: 'unread', label: '미확인' },
            { key: 'read', label: '확인' },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setFilter(tab.key)}
              className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                filter === tab.key
                  ? 'bg-white text-gray-800 shadow-sm font-medium'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="text-center text-gray-400 py-12">불러오는 중...</div>
      ) : filteredAlerts.length === 0 ? (
        <div className="text-center py-16">
          <div className="text-4xl mb-3">🔔</div>
          <p className="text-gray-400 text-sm">
            {filter === 'unread' ? '미확인 알림이 없습니다.' : '알림이 없습니다.'}
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {filteredAlerts.map((alert) => {
            const review = alert.review;
            const formattedDate = new Date(alert.created_at).toLocaleString('ko-KR');

            return (
              <button
                key={alert.id}
                onClick={() => handleClick(alert)}
                className={`w-full text-left rounded-lg p-4 border transition-colors ${
                  alert.is_read
                    ? 'bg-white border-gray-200 hover:bg-gray-50'
                    : 'bg-red-50 border-red-200 hover:bg-red-100'
                }`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1.5">
                      {!alert.is_read && (
                        <span className="w-2 h-2 bg-red-500 rounded-full flex-shrink-0" />
                      )}
                      <span className="text-sm font-medium text-gray-800">
                        {alert.type === 'low_rating' ? '⚠️ 저평점 리뷰' : '알림'}
                      </span>
                      {review && <PlatformBadge platform={review.platform} />}
                      {review && (
                        <StarRating rating={review.rating} scale={review.rating_scale} />
                      )}
                    </div>

                    {review && (
                      <>
                        <p className="text-sm text-gray-600 truncate mb-1">
                          {review.content || '(내용 없음)'}
                        </p>
                        <span className="text-xs text-gray-400">
                          작성자: {review.author || '익명'}
                        </span>
                      </>
                    )}
                  </div>

                  <span className="text-xs text-gray-400 whitespace-nowrap flex-shrink-0">
                    {formattedDate}
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
