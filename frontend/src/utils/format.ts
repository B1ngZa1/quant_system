// 格式化工具函数

// 格式化金额
export const formatMoney = (amount: number, decimals = 2): string => {
  if (amount === null || amount === undefined) return '-'
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  }).format(amount)
}

// 格式化数量
export const formatNumber = (num: number, decimals = 0): string => {
  if (num === null || num === undefined) return '-'
  return new Intl.NumberFormat('zh-CN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  }).format(num)
}

// 格式化成交量
export const formatVolume = (volume: number): string => {
  if (volume >= 100000000) {
    return (volume / 100000000).toFixed(2) + '亿'
  } else if (volume >= 10000) {
    return (volume / 10000).toFixed(2) + '万'
  }
  return volume.toString()
}

// 格式化百分比
export const formatPercent = (value: number, decimals = 2, withSign = true): string => {
  if (value === null || value === undefined) return '-'
  const formatted = (value * 100).toFixed(decimals)
  return withSign && value > 0 ? `+${formatted}%` : `${formatted}%`
}

// 格式化涨跌幅颜色
export const getChangeColor = (value: number): string => {
  if (value > 0) return 'up'
  if (value < 0) return 'down'
  return 'neutral'
}

// 格式化日期
export const formatDate = (date: string | Date, format = 'YYYY-MM-DD'): string => {
  if (!date) return '-'
  const d = new Date(date)
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hour = String(d.getHours()).padStart(2, '0')
  const minute = String(d.getMinutes()).padStart(2, '0')
  
  return format
    .replace('YYYY', String(year))
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hour)
    .replace('mm', minute)
}
