import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getReview } from '../api/client';
import StarRating from '../components/StarRating';
import PlatformBadge from '../components/PlatformBadge';

export default function ReviewDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [review, setReview] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getReview(id)
      .then((res) => setReview(res.data))
      .catch((err) => {
        console.error('리뷰 조회 실패:', err);
        alert('리뷰를 찾을 수 없습니다.');
        navigate('/');
      })
      .finally(() => setLoading(false));
  }, [id, navigate]);

  if (loading) {
    return <div className="text-center text-gray-400 py-12">불러오는 중...</div>;
  }

  if (!review) return null;

  const formattedDate = review.reviewed_at
    ? new Date(review.reviewed_at).toLocaleString('ko-KR')
    : '';

  return (
    <div className="max-w-3xl">
      {/* 뒤로가기 */}
      <button
        onClick={() => navigate('/')}
        className="text-sm text-gray-500 hover:text-gray-700 mb-4 flex items-center gap-1"
      >
        ← 대시보드로 돌아가기
      </button>

      {/* 리뷰 카드 */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <PlatformBadge platform={review.platform} />
            <StarRating rating={review.rating} scale={review.rating_scale} />
          </div>
          <span className="text-sm text-gray-400">{formattedDate}</span>
        </div>

        <p className="text-gray-800 leading-relaxed mb-4">{review.content}</p>

        <div className="flex items-center justify-between pt-4 border-t border-gray-100">
          <span className="text-sm text-gray-500">작성자: {review.author}</span>
          {review.is_replied ? (
            <span className="text-sm text-green-600 bg-green-50 px-3 py-1 rounded">답변 완료</span>
          ) : (
            <span className="text-sm text-orange-600 bg-orange-50 px-3 py-1 rounded">미답변</span>
          )}
        </div>
      </div>

      {/* AI 댓글 생성 영역 (Phase 3에서 구현) */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">AI 댓글 생성</h3>
        <p className="text-gray-400 text-sm">Phase 3에서 AI 댓글 생성 기능이 이곳에 구현됩니다.</p>
      </div>
    </div>
  );
}
