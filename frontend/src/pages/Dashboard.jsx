import { useState, useEffect, useCallback } from 'react';
import { getReviews, getReviewStats, syncReviews, batchAutoReply } from '../api/client';
import ReviewCard from '../components/ReviewCard';
import FilterBar from '../components/FilterBar';

export default function Dashboard() {
  const [reviews, setReviews] = useState([]);
  const [stats, setStats] = useState(null);
  const [filters, setFilters] = useState({ platform: '', rating: '', sort: 'latest', is_replied: '', page: 1 });
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [batching, setBatching] = useState(false);
  const pageSize = 12;

  const fetchReviews = useCallback(async () => {
    setLoading(true);
    try {
      const params = { sort: filters.sort, page: filters.page, size: pageSize };
      if (filters.platform) params.platform = filters.platform;
      if (filters.rating) {
        params.min_rating = Number(filters.rating);
        params.max_rating = Number(filters.rating);
      }
      if (filters.is_replied !== '') params.is_replied = filters.is_replied;

      const res = await getReviews(params);
      setReviews(res.data.items);
      setTotal(res.data.total);
    } catch (err) {
      console.error('리뷰 목록 조회 실패:', err);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  const fetchStats = async () => {
    try {
      const res = await getReviewStats();
      setStats(res.data);
    } catch (err) {
      console.error('통계 조회 실패:', err);
    }
  };

  useEffect(() => {
    fetchReviews();
  }, [fetchReviews]);

  useEffect(() => {
    fetchStats();
  }, []);

  const handleSync = async () => {
    setSyncing(true);
    try {
      const res = await syncReviews();
      alert(`동기화 완료: 신규 ${res.data.new_reviews}건`);
      fetchReviews();
      fetchStats();
    } catch (err) {
      alert('동기화 실패: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSyncing(false);
    }
  };

  const handleBatch = async () => {
    setBatching(true);
    try {
      const res = await batchAutoReply();
      const d = res.data;
      alert(`일괄 처리 완료: 총 ${d.total}건 (성공 ${d.success}, 보류 ${d.held}, 승인대기 ${d.pending}, 실패 ${d.failed})`);
      fetchReviews();
      fetchStats();
    } catch (err) {
      alert('일괄 처리 실패: ' + (err.response?.data?.detail || err.message));
    } finally {
      setBatching(false);
    }
  };

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div>
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-800">리뷰 대시보드</h2>
        <div className="flex gap-2">
          <button
            onClick={handleSync}
            disabled={syncing}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors flex items-center gap-2"
          >
            {syncing ? (
              <>
                <span className="animate-spin">↻</span> 동기화 중...
              </>
            ) : (
              <>🔄 리뷰 동기화</>
            )}
          </button>
          <button
            onClick={handleBatch}
            disabled={batching}
            className="bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50 transition-colors flex items-center gap-2"
          >
          {batching ? (
            <>
              <span className="animate-spin">↻</span> 처리 중...
            </>
          ) : (
            <>⚡ 미답변 리뷰 처리</>
          )}
          </button>
        </div>
      </div>

      {/* 통계 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow p-5">
          <p className="text-sm text-gray-500">총 리뷰 수</p>
          <p className="text-3xl font-bold text-gray-800 mt-1">
            {stats ? stats.total_count.toLocaleString() : '-'}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-5">
          <p className="text-sm text-gray-500">평균 별점</p>
          <p className="text-3xl font-bold text-gray-800 mt-1">
            {stats ? `⭐ ${stats.average_rating}` : '-'}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-5">
          <p className="text-sm text-gray-500">미답변 리뷰</p>
          <p className="text-3xl font-bold text-orange-600 mt-1">
            {stats ? stats.unreplied_count : '-'}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-5">
          <p className="text-sm text-gray-500 mb-2">플랫폼별</p>
          {stats?.platform_stats?.length > 0 ? (
            <div className="space-y-1">
              {stats.platform_stats.map((p) => (
                <div key={p.platform} className="flex justify-between text-sm">
                  <span className="text-gray-600">
                    {p.platform === 'naver' ? '네이버' : p.platform === 'modudoc' ? '모두닥' : '굿닥'}
                  </span>
                  <span className="text-gray-800 font-medium">{p.count}건 (⭐{p.avg_rating})</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-400 text-sm">-</p>
          )}
        </div>
      </div>

      {/* 필터바 */}
      <FilterBar filters={filters} onChange={setFilters} />

      {/* 리뷰 목록 */}
      {loading ? (
        <div className="text-center text-gray-400 py-12">불러오는 중...</div>
      ) : reviews.length === 0 ? (
        <div className="text-center text-gray-400 py-12">
          리뷰가 없습니다. "리뷰 동기화" 버튼을 눌러 리뷰를 가져와보세요.
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
            {reviews.map((review) => (
              <ReviewCard key={review.id} review={review} />
            ))}
          </div>

          {/* 페이지네이션 */}
          {totalPages > 1 && (
            <div className="flex justify-center gap-2">
              <button
                onClick={() => setFilters((f) => ({ ...f, page: f.page - 1 }))}
                disabled={filters.page <= 1}
                className="px-3 py-1 rounded border text-sm disabled:opacity-30"
              >
                ← 이전
              </button>
              {Array.from({ length: Math.min(totalPages, 10) }, (_, i) => {
                const pageNum = i + 1;
                return (
                  <button
                    key={pageNum}
                    onClick={() => setFilters((f) => ({ ...f, page: pageNum }))}
                    className={`px-3 py-1 rounded border text-sm ${
                      filters.page === pageNum
                        ? 'bg-blue-600 text-white border-blue-600'
                        : 'hover:bg-gray-50'
                    }`}
                  >
                    {pageNum}
                  </button>
                );
              })}
              <button
                onClick={() => setFilters((f) => ({ ...f, page: f.page + 1 }))}
                disabled={filters.page >= totalPages}
                className="px-3 py-1 rounded border text-sm disabled:opacity-30"
              >
                다음 →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
