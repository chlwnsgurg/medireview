import { useEffect, useState } from 'react';
import { getAutomationRules, updateAutomationRules, getAutomationLogs } from '../api/client';

const STATUS_MAP = {
  posted: { label: '자동 등록 완료', icon: '✅', color: 'text-green-600' },
  pending_approval: { label: '승인 대기', icon: '⏳', color: 'text-yellow-600' },
  held: { label: '보류', icon: '🚫', color: 'text-red-600' },
  approved: { label: '승인 후 등록', icon: '✅', color: 'text-green-600' },
  failed: { label: '실패', icon: '❌', color: 'text-red-500' },
};

const STYLE_OPTIONS = [
  { value: 'empathy', label: '공감 및 감사형' },
  { value: 'guidance', label: '안내 및 개선 약속형' },
  { value: 'apology', label: '사과 및 해명형' },
];

export default function AutomationSettings() {
  const [rule, setRule] = useState(null);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [newKeyword, setNewKeyword] = useState('');

  useEffect(() => {
    Promise.all([
      getAutomationRules().catch(() => ({ data: null })),
      getAutomationLogs().catch(() => ({ data: [] })),
    ])
      .then(([rulesRes, logsRes]) => {
        if (rulesRes.data) {
          setRule({
            ...rulesRes.data,
            hold_keywords: JSON.parse(rulesRes.data.hold_keywords || '[]'),
          });
        }
        setLogs(logsRes.data);
      })
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setMessage('');
    try {
      await updateAutomationRules({
        is_enabled: rule.is_enabled,
        auto_reply_style: rule.auto_reply_style,
        hold_keywords: JSON.stringify(rule.hold_keywords),
        require_approval: rule.require_approval,
      });
      setMessage('저장되었습니다.');
    } catch {
      setMessage('저장에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  const addKeyword = () => {
    const kw = newKeyword.trim();
    if (kw && !rule.hold_keywords.includes(kw)) {
      setRule({ ...rule, hold_keywords: [...rule.hold_keywords, kw] });
      setNewKeyword('');
    }
  };

  const removeKeyword = (kw) => {
    setRule({ ...rule, hold_keywords: rule.hold_keywords.filter((k) => k !== kw) });
  };

  if (loading) return <div className="text-center text-gray-400 py-12">불러오는 중...</div>;
  if (!rule) return <div className="text-center text-gray-400 py-12">병원 정보를 먼저 등록해주세요.</div>;

  return (
    <div className="max-w-3xl">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">자동화 설정</h2>

      {/* 설정 폼 */}
      <div className="bg-white rounded-lg shadow p-6 mb-6 space-y-6">
        {/* ON/OFF 토글 */}
        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium text-gray-800">자동 대응</p>
            <p className="text-sm text-gray-400">새 리뷰에 AI가 자동으로 답변을 생성하고 등록합니다</p>
          </div>
          <button
            onClick={() => setRule({ ...rule, is_enabled: !rule.is_enabled })}
            className={`relative w-14 h-7 rounded-full transition-colors ${
              rule.is_enabled ? 'bg-indigo-600' : 'bg-gray-300'
            }`}
          >
            <span className={`absolute top-0.5 left-0.5 w-6 h-6 bg-white rounded-full shadow transition-transform ${
              rule.is_enabled ? 'translate-x-7' : ''
            }`} />
          </button>
        </div>

        {/* 기본 댓글 스타일 */}
        <div>
          <p className="font-medium text-gray-800 mb-3">기본 댓글 스타일</p>
          <div className="space-y-2">
            {STYLE_OPTIONS.map((opt) => (
              <label key={opt.value} className="flex items-center gap-3 cursor-pointer">
                <input
                  type="radio"
                  name="style"
                  checked={rule.auto_reply_style === opt.value}
                  onChange={() => setRule({ ...rule, auto_reply_style: opt.value })}
                  className="w-4 h-4 text-indigo-600"
                />
                <span className="text-sm text-gray-700">{opt.label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* 관리자 승인 */}
        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium text-gray-800">관리자 승인 필요</p>
            <p className="text-sm text-gray-400">AI가 댓글을 생성한 뒤 관리자가 승인해야 등록됩니다</p>
          </div>
          <button
            onClick={() => setRule({ ...rule, require_approval: !rule.require_approval })}
            className={`relative w-14 h-7 rounded-full transition-colors ${
              rule.require_approval ? 'bg-indigo-600' : 'bg-gray-300'
            }`}
          >
            <span className={`absolute top-0.5 left-0.5 w-6 h-6 bg-white rounded-full shadow transition-transform ${
              rule.require_approval ? 'translate-x-7' : ''
            }`} />
          </button>
        </div>

        {/* 보류 키워드 */}
        <div>
          <p className="font-medium text-gray-800 mb-3">대응 보류 키워드</p>
          <p className="text-sm text-gray-400 mb-2">이 키워드가 포함된 리뷰는 자동 대응을 보류합니다</p>
          <div className="flex flex-wrap gap-2 mb-3">
            {rule.hold_keywords.map((kw) => (
              <span key={kw} className="inline-flex items-center gap-1 px-3 py-1 bg-gray-100 rounded-full text-sm text-gray-700">
                {kw}
                <button onClick={() => removeKeyword(kw)} className="text-gray-400 hover:text-red-500 ml-1">✕</button>
              </span>
            ))}
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              value={newKeyword}
              onChange={(e) => setNewKeyword(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && addKeyword()}
              placeholder="키워드 입력"
              className="flex-1 px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
            <button
              onClick={addKeyword}
              className="px-4 py-2 bg-gray-100 text-sm rounded-lg hover:bg-gray-200"
            >추가</button>
          </div>
        </div>

        {/* 저장 */}
        {message && (
          <p className={`text-sm ${message.includes('실패') ? 'text-red-500' : 'text-green-600'}`}>{message}</p>
        )}
        <button
          onClick={handleSave}
          disabled={saving}
          className="w-full py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 font-medium"
        >
          {saving ? '저장 중...' : '설정 저장'}
        </button>
      </div>

      {/* 자동 대응 로그 */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">자동 대응 로그</h3>
        {logs.length === 0 ? (
          <p className="text-gray-400 text-sm">아직 자동 대응 기록이 없습니다.</p>
        ) : (
          <div className="space-y-3">
            {logs.map((log) => {
              const st = STATUS_MAP[log.status] || { label: log.status, icon: '•', color: 'text-gray-500' };
              return (
                <div key={log.id} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center gap-3">
                    <span className="text-lg">{st.icon}</span>
                    <div>
                      <p className={`text-sm font-medium ${st.color}`}>{st.label}</p>
                      <p className="text-xs text-gray-400">
                        리뷰 #{log.review_id}
                        {log.reason && ` · ${log.reason}`}
                      </p>
                    </div>
                  </div>
                  <span className="text-xs text-gray-400">
                    {new Date(log.created_at).toLocaleString('ko-KR')}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
