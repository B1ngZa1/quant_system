import dayjs from 'dayjs'
import utc from 'dayjs/plugin/utc'
import timezone from 'dayjs/plugin/timezone'
import 'dayjs/locale/zh-cn'

dayjs.extend(utc)
dayjs.extend(timezone)
dayjs.locale('zh-cn')

/**
 * 上海证券交易所 A 股常规交易时段（Asia/Shanghai）：
 * - 周一至周五：9:30–11:30、13:00–15:00 为连续竞价（盘中）
 * - 周末：休市
 * 法定节假日未内置，如需可后续接入节假日历。
 */
export function getCnAshareSessionLabel(nowCn?: dayjs.Dayjs): string {
  const now = nowCn ?? dayjs().tz('Asia/Shanghai')
  const dow = now.day()
  if (dow === 0 || dow === 6) {
    return 'A股今日休市（周末）'
  }

  const hm = now.hour() * 60 + now.minute()
  const morningStart = 9 * 60 + 30 // 09:30
  const morningEnd = 11 * 60 + 30 // 11:30
  const afternoonStart = 13 * 60 // 13:00
  const afternoonEnd = 15 * 60 // 15:00

  if (hm >= morningStart && hm <= morningEnd) {
    return 'A股盘中'
  }
  if (hm >= afternoonStart && hm <= afternoonEnd) {
    return 'A股盘中'
  }
  if (hm > morningEnd && hm < afternoonStart) {
    return 'A股午间休市'
  }
  return 'A股非交易时段（盘前或已收盘）'
}

/** 首页日期展示（中国时区、中文星期） */
export function formatCnDashboardDate(nowCn?: dayjs.Dayjs): string {
  const now = nowCn ?? dayjs().tz('Asia/Shanghai')
  return now.format('MM月DD日 dddd')
}
