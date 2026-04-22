import { useNavigate } from 'react-router';
import StarRating from '@medireview/components/StarRating';
import PlatformBadge from '@medireview/components/PlatformBadge';

const REVIEW_TYPE_BADGE = {
  positive: { label: '호감', color: 'text-green-600 bg-green-50' },
  complaint: { label: '컴플레인', color: 'text-orange-600 bg-orange-50' },
  claim: { label: '클레임', color: 'text-red-600 bg-red-50' },
};

export default function ReviewCard({ review }) {
  const navigate = useNavigate();

  const formattedDate = review.reviewed_at
    ? new Date(review.reviewed_at).toLocaleDateString('ko-KR')
    : '';

  const typeBadge = REVIEW_TYPE_BADGE[review.review_type] || null;

  return (
    <div
      onClick={() => navigate(`/reviews/${review.id}`)}
      className="bg-white rounded-lg shadow hover:shadow-md transition-shadow p-5 cursor-pointer border border-gray-100"
    >
      {/* 상단: 플랫폼 + 별점 + 날짜 */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <PlatformBadge platform={review.platform} />
          <StarRating rating={review.rating} scale={review.rating_scale} />
          {typeBadge && (
            <span className={`text-xs px-2 py-0.5 rounded ${typeBadge.color}`}>
              {typeBadge.label}
            </span>
          )}
        </div>
        <span className="text-xs text-gray-400">{formattedDate}</span>
      </div>

      {/* 내용 */}
      <p className="text-sm text-gray-700 line-clamp-2 mb-3">{review.content}</p>

      {/* 하단: 작성자 + 답변 상태 */}
      <div className="flex items-center justify-between">
        <span className="text-xs text-gray-400">{review.author}</span>
        {review.is_replied ? (
          <span className="text-xs text-green-600 bg-green-50 px-2 py-0.5 rounded">답변 완료</span>
        ) : (
          <span className="text-xs text-orange-600 bg-orange-50 px-2 py-0.5 rounded">미답변</span>
        )}
      </div>
    </div>
  );
}
