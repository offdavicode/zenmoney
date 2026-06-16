import { EMOTIONS } from '@/utils/constants';

interface EmotionTagProps {
  emotionId: string;
  size?: 'sm' | 'md';
}

export function EmotionTag({ emotionId, size = 'sm' }: EmotionTagProps) {
  const emotion = EMOTIONS.find((e) => e.id === emotionId);

  if (!emotion) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-surface-hover px-2 py-0.5 text-xs text-muted">
        Não especificada
      </span>
    );
  }

  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm';

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full font-medium ${sizeClasses} transition-transform hover:scale-105`}
      style={{
        backgroundColor: `${emotion.color}15`,
        color: emotion.color,
        border: `1px solid ${emotion.color}30`,
      }}
    >
      {emotion.label}
    </span>
  );
}
