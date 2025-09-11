import { competencyLabels, scoreRanges } from '../data/data'

interface CompetencyChartProps {
  competencyScores: {
    empathy_compassion: number
    safety_awareness: number
    communication_skills: number
    problem_solving: number
    experience_commitment: number
  }
}

export function CompetencyChart({ competencyScores }: CompetencyChartProps) {
  const getScoreColor = (score: number) => {
    if (score >= 8) return scoreRanges.excellent
    if (score >= 6) return scoreRanges.good
    if (score >= 4) return scoreRanges.fair
    return scoreRanges.poor
  }

  const maxScore = 10
  const chartHeight = 300
  const barWidth = 60
  const spacing = 40

  return (
    <div className="w-full">
      {/* Chart */}
      <div className="relative bg-gray-50 dark:bg-gray-900 rounded-lg p-6 mb-6">
        <svg 
          width="100%" 
          height={chartHeight + 60}
          viewBox={`0 0 ${(barWidth + spacing) * Object.keys(competencyScores).length} ${chartHeight + 60}`}
          className="overflow-visible"
        >
          {/* Grid lines */}
          {[0, 2, 4, 6, 8, 10].map((value) => (
            <g key={value}>
              <line
                x1={0}
                y1={chartHeight - (value / maxScore) * chartHeight + 20}
                x2={(barWidth + spacing) * Object.keys(competencyScores).length}
                y2={chartHeight - (value / maxScore) * chartHeight + 20}
                stroke="#e5e7eb"
                strokeWidth={1}
                strokeDasharray={value === 0 ? "none" : "2,2"}
              />
              <text
                x={-10}
                y={chartHeight - (value / maxScore) * chartHeight + 25}
                textAnchor="end"
                className="text-xs fill-gray-500"
              >
                {value}
              </text>
            </g>
          ))}

          {/* Bars */}
          {Object.entries(competencyScores).map(([key, score], index) => {
            const scoreColor = getScoreColor(score)
            const barHeight = (score / maxScore) * chartHeight
            const x = index * (barWidth + spacing) + spacing / 2
            
            return (
              <g key={key}>
                {/* Bar */}
                <rect
                  x={x}
                  y={chartHeight - barHeight + 20}
                  width={barWidth}
                  height={barHeight}
                  className={`${scoreColor.bgColor.replace('bg-', 'fill-')} opacity-80`}
                  rx={4}
                />
                
                {/* Score label on top of bar */}
                <text
                  x={x + barWidth / 2}
                  y={chartHeight - barHeight + 10}
                  textAnchor="middle"
                  className={`text-sm font-bold ${scoreColor.color.replace('text-', 'fill-')}`}
                >
                  {score}
                </text>
                
                {/* Competency label */}
                <text
                  x={x + barWidth / 2}
                  y={chartHeight + 40}
                  textAnchor="middle"
                  className="text-xs fill-gray-700 dark:fill-gray-300"
                  style={{ fontSize: '10px' }}
                >
                  {competencyLabels[key as keyof typeof competencyLabels]
                    .split(' ')
                    .map((word, i) => (
                      <tspan key={i} x={x + barWidth / 2} dy={i === 0 ? 0 : 12}>
                        {word}
                      </tspan>
                    ))}
                </text>
              </g>
            )
          })}
        </svg>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap justify-center gap-4 text-xs">
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded ${scoreRanges.excellent.bgColor}`} />
          <span>Excellent (8-10)</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded ${scoreRanges.good.bgColor}`} />
          <span>Good (6-7)</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded ${scoreRanges.fair.bgColor}`} />
          <span>Fair (4-5)</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded ${scoreRanges.poor.bgColor}`} />
          <span>Poor (0-3)</span>
        </div>
      </div>

      {/* Detailed Breakdown */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
        {Object.entries(competencyScores).map(([key, score]) => {
          const scoreColor = getScoreColor(score)
          const label = competencyLabels[key as keyof typeof competencyLabels]
          const percentage = (score / maxScore) * 100
          
          return (
            <div key={key} className="p-4 border rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-medium text-sm">{label}</h4>
                <span className={`font-bold ${scoreColor.color}`}>
                  {score}/10
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${scoreColor.bgColor} border ${scoreColor.color.replace('text-', 'border-')}`}
                  style={{ width: `${percentage}%` }}
                />
              </div>
              <div className="mt-1 text-xs text-muted-foreground">
                {percentage.toFixed(0)}% of maximum score
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
