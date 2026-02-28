import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getReview, generateComments, getComments, postComment } from '../api/client';
import StarRating from '../components/StarRating';
import PlatformBadge from '../components/PlatformBadge';

const STYLE_LABELS = {
  empathy: { label: '공감형', color: 'bg-blue-100 text-blue-700' },
  guidance: { label: '안내형', color: 'bg-emerald-100 text-emerald-700' },
  apology: { label: '사과형', color: 'bg-amber-100 text-amber-700' },
};

export default function ReviewDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [review, setReview] = useState(null);
  const [loading, setLoading] = useState(true);

  // 댓글 관련 state
  const [comments, setComments] = useState([]);
  const [generating, setGenerating] = useState(false);
  const [editedContents, setEditedContents] = useState({});
  const [copiedId, setCopiedId] = useState(null);
  const [posting, setPosting] = useState(false);

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

  // 기존 댓글 불러오기
  useEffect(() => {
    if (id) {
      getComments(id)
        .then((res) => setComments(res.data))
        .catch(() => {});
    }
  }, [id]);

  // AI 댓글 생성
  const handleGenerate = async () => {
    setGenerating(true);
    setEditedContents({});
    try {
      const res = await generateComments(id);
      setComments(res.data);
    } catch (err) {
      console.error('댓글 생성 실패:', err);
      alert('AI 댓글 생성에 실패했습니다. 잠시 후 다시 시도해주세요.');
    } finally {
      setGenerating(false);
    }
  };

  // 클립보드 복사
  const handleCopy = async (comment) => {
    const text = editedContents[comment.id] ?? comment.content;
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(comment.id);
      setTimeout(() => setCopiedId(null), 2000);
    } catch {
      // fallback
      const ta = document.createElement('textarea');
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      setCopiedId(comment.id);
      setTimeout(() => setCopiedId(null), 2000);
    }
  };

  // 등록 완료 처리
  const handlePost = async (comment) => {
    if (!confirm('이 댓글을 등록 완료 처리하시겠습니까?\n(플랫폼에 직접 붙여넣은 후 눌러주세요)')) return;
    setPosting(true);
    try {
      await postComment(id, comment.id);
      // 리뷰 + 댓글 상태 갱신
      const [reviewRes, commentsRes] = await Promise.all([
        getReview(id),
        getComments(id),
      ]);
      setReview(reviewRes.data);
      setComments(commentsRes.data);
    } catch (err) {
      console.error('등록 실패:', err);
      alert('등록 처리에 실패했습니다.');
    } finally {
      setPosting(false);
    }
  };

  // 댓글 내용 수정
  const handleEdit = (commentId, value) => {
    setEditedContents((prev) => ({ ...prev, [commentId]: value }));
  };

  if (loading) {
    return <div className="text-center text-gray-400 py-12">불러오는 중...</div>;
  }

  if (!review) return null;

  const formattedDate = review.reviewed_at
    ? new Date(review.reviewed_at).toLocaleString('ko-KR')
    : '';

  const postedComment = comments.find((c) => c.is_posted);

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
            className="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {generating ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                생성 중...
              </span>
            ) : comments.length > 0 ? '재생성' : '댓글 생성하기'}
          </button>
        </div>

        {/* 등록된 댓글 표시 */}
        {postedComment && (
          <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-green-700 text-sm font-medium">✓ 등록 완료된 댓글</span>
              <span className={`text-xs px-2 py-0.5 rounded-full ${STYLE_LABELS[postedComment.style]?.color || 'bg-gray-100 text-gray-600'}`}>
                {STYLE_LABELS[postedComment.style]?.label || postedComment.style}
              </span>
            </div>
            <p className="text-gray-700 text-sm leading-relaxed">{postedComment.content}</p>
          </div>
        )}

        {/* 댓글 후보 목록 */}
        {comments.length > 0 && !generating ? (
          <div className="space-y-4">
            {comments
              .filter((c) => !c.is_posted)
              .map((comment) => {
                const styleInfo = STYLE_LABELS[comment.style] || { label: comment.style, color: 'bg-gray-100 text-gray-600' };
                return (
                  <div key={comment.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${styleInfo.color}`}>
                        {styleInfo.label}
                      </span>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleCopy(comment)}
                          className="text-xs px-3 py-1.5 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                        >
                          {copiedId === comment.id ? '✓ 복사됨' : '📋 복사'}
                        </button>
                        <button
                          onClick={() => handlePost(comment)}
                          disabled={posting}
                          className="text-xs px-3 py-1.5 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 transition-colors"
                        >
                          등록 완료
                        </button>
                      </div>
                    </div>
                    <textarea
                      value={editedContents[comment.id] ?? comment.content}
                      onChange={(e) => handleEdit(comment.id, e.target.value)}
                      rows={4}
                      className="w-full text-sm text-gray-700 border border-gray-200 rounded-md p-3 resize-y focus:outline-none focus:ring-2 focus:ring-indigo-300 focus:border-indigo-300"
                    />
                  </div>
                );
              })}
          </div>
        ) : !generating ? (
          <p className="text-gray-400 text-sm text-center py-6">
            AI 댓글 생성 버튼을 눌러 답변 초안을 만들어 보세요.
          </p>
        ) : null}

        {generating && (
          <div className="text-center py-8">
            <svg className="animate-spin h-8 w-8 text-indigo-500 mx-auto mb-3" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <p className="text-gray-500 text-sm">Gemini가 댓글을 생성하고 있습니다...</p>
          </div>
        )}
      </div>
    </div>
  );
}
