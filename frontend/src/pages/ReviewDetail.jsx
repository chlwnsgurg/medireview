import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getReview, generateComments, getComments, postComment } from '../api/client';
import StarRating from '../components/StarRating';
import PlatformBadge from '../components/PlatformBadge';

const STYLE_LABELS = {
  empathy: { label: '공감형', color: 'bg-blue-100 text-blue-700' },
  guidance: { label: '안내형', color: 'bg-green-100 text-green-700' },
  apology: { label: '사과형', color: 'bg-orange-100 text-orange-700' },
};

export default function ReviewDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [review, setReview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [comments, setComments] = useState([]);
  const [generating, setGenerating] = useState(false);
  const [posting, setPosting] = useState(false);
  const [selectedId, setSelectedId] = useState(null);
  const [message, setMessage] = useState('');

  useEffect(() => {
    Promise.all([
      getReview(id),
      getComments(id).catch(() => ({ data: [] })),
    ])
      .then(([reviewRes, commentsRes]) => {
        setReview(reviewRes.data);
        setComments(commentsRes.data);
      })
      .catch((err) => {
        console.error('리뷰 조회 실패:', err);
        alert('리뷰를 찾을 수 없습니다.');
        navigate('/');
      })
      .finally(() => setLoading(false));
  }, [id, navigate]);

  const handleGenerate = async () => {
    setGenerating(true);
    setMessage('');
    try {
      const res = await generateComments(id);
      setComments(res.data);
    } catch (err) {
      setMessage('AI 댓글 생성에 실패했습니다.');
      console.error(err);
    } finally {
      setGenerating(false);
    }
  };

  const handlePost = async (commentId) => {
    setPosting(true);
    setMessage('');
    try {
      await postComment(id, commentId);
      setMessage('댓글이 네이버에 등록되었습니다!');
      // 리뷰 상태 갱신
      const res = await getReview(id);
      setReview(res.data);
      const cRes = await getComments(id);
      setComments(cRes.data);
    } catch (err) {
      setMessage(err.response?.data?.detail || '댓글 등록에 실패했습니다.');
      console.error(err);
    } finally {
      setPosting(false);
    }
  };

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

      {/* AI 댓글 생성 영역 */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-800">AI 댓글 생성</h3>
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {generating ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                생성 중...
              </span>
            ) : comments.length > 0 ? '재생성' : 'AI 답변 생성'}
          </button>
        </div>

        {/* 메시지 */}
        {message && (
          <div className={`mb-4 p-3 rounded text-sm ${
            message.includes('실패') ? 'bg-red-50 text-red-600' : 'bg-green-50 text-green-600'
          }`}>
            {message}
          </div>
        )}

        {/* 댓글 목록 */}
        {comments.length === 0 ? (
          <p className="text-gray-400 text-sm">
            "AI 답변 생성" 버튼을 클릭하면 3가지 스타일의 답변이 생성됩니다.
          </p>
        ) : (
          <div className="space-y-4">
            {comments.map((c) => {
              const styleInfo = STYLE_LABELS[c.style] || { label: c.style, color: 'bg-gray-100 text-gray-700' };
              const isSelected = selectedId === c.id;
              return (
                <div
                  key={c.id}
                  onClick={() => !c.is_posted && setSelectedId(c.id)}
                  className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                    c.is_posted
                      ? 'border-green-300 bg-green-50 cursor-default'
                      : isSelected
                        ? 'border-indigo-400 bg-indigo-50'
                        : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className={`text-xs font-medium px-2 py-1 rounded ${styleInfo.color}`}>
                      {styleInfo.label}
                    </span>
                    {c.is_posted && (
                      <span className="text-xs text-green-600 font-medium">✓ 등록 완료</span>
                    )}
                  </div>
                  <p className="text-gray-700 text-sm leading-relaxed">{c.content}</p>
                </div>
              );
            })}

            {/* 등록 버튼 */}
            {!review.is_replied && selectedId && (
              <button
                onClick={() => handlePost(selectedId)}
                disabled={posting}
                className="w-full py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
              >
                {posting ? '등록 중...' : '선택한 답변 네이버에 등록'}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
