import { useParams } from 'react-router-dom';

export default function ReviewDetail() {
  const { id } = useParams();

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-6">리뷰 상세 #{id}</h2>
      <p className="text-gray-400 text-sm">Phase 2~3에서 리뷰 상세 및 AI 댓글 기능이 이곳에 구현됩니다.</p>
    </div>
  );
}
