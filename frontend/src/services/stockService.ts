// 股票相关API服务

import { api } from './api'
import type {
  Stock,
  StockPrice,
  StockHistoryData,
  TechnicalIndicators,
  PaginatedResponse,
  PaginationParams,
} from '@types/index'
import type {
  StockListRequest,
  StockPriceRequest,
  StockHistoryRequest,
  TechnicalIndicatorsRequest,
  MarketOverviewRequest,
  StockSearchRequest,
} from '@types/api'

// 股票列表
export const getStockList = async (
  params: StockListRequest & PaginationParams
): Promise<PaginatedResponse<Stock>> => {
  return api.get('/stocks', params)
}

// 获取单个股票信息
export const getStock = async (symbol: string): Promise<Stock> => {
  return api.get(`/stocks/${symbol}`)
}

// 搜索股票
export const searchStocks = async (params: StockSearchRequest): Promise<Stock[]> => {
  return api.get('/stocks/search', params)
}

// 获取股票实时价格
export const getStockPrice = async (params: StockPriceRequest): Promise<StockPrice[]> => {
  return api.get('/stocks/prices', params)
}

// 获取单个股票实时价格
export const getStockPriceBySymbol = async (symbol: string): Promise<StockPrice> => {
  return api.get(`/stocks/${symbol}/price`)
}

// 获取股票历史数据
export const getStockHistory = async (
  symbol: string,
  params: StockHistoryRequest
): Promise<StockHistoryData[]> => {
  return api.get(`/stocks/${symbol}/history`, params)
}

// 获取技术指标
export const getTechnicalIndicators = async (
  symbol: string,
  params: TechnicalIndicatorsRequest
): Promise<TechnicalIndicators> => {
  return api.get(`/stocks/${symbol}/indicators`, params)
}

// 获取市场概览
export const getMarketOverview = async (params?: MarketOverviewRequest): Promise<{
  total_stocks: number
  active_stocks: number
  market_cap: number
  total_volume: number
  gainers: Stock[]
  losers: Stock[]
  most_active: Stock[]
  sector_performance: Array<{
    sector: string
    change_percent: number
    volume: number
  }>
}> => {
  return api.get('/market/overview', params)
}

// 获取热门股票
export const getHotStocks = async (limit: number = 10): Promise<Stock[]> => {
  return api.get('/stocks/hot', { limit })
}

// 获取涨幅榜
export const getGainers = async (limit: number = 10): Promise<Stock[]> => {
  return api.get('/stocks/gainers', { limit })
}

// 获取跌幅榜
export const getLosers = async (limit: number = 10): Promise<Stock[]> => {
  return api.get('/stocks/losers', { limit })
}

// 获取成交量排行
export const getMostActive = async (limit: number = 10): Promise<Stock[]> => {
  return api.get('/stocks/most-active', { limit })
}

// 获取行业分类
export const getSectors = async (): Promise<Array<{
  id: string
  name: string
  stock_count: number
  market_cap: number
  change_percent: number
}>> => {
  return api.get('/stocks/sectors')
}

// 获取行业内股票
export const getStocksBySector = async (
  sector: string,
  params?: PaginationParams
): Promise<PaginatedResponse<Stock>> => {
  return api.get(`/stocks/sectors/${sector}`, params)
}

// 添加股票到关注列表
export const addToWatchlist = async (symbol: string): Promise<void> => {
  return api.post('/stocks/watchlist', { symbol })
}

// 从关注列表移除股票
export const removeFromWatchlist = async (symbol: string): Promise<void> => {
  return api.delete(`/stocks/watchlist/${symbol}`)
}

// 获取关注列表
export const getWatchlist = async (): Promise<Stock[]> => {
  return api.get('/stocks/watchlist')
}

// 获取股票新闻
export const getStockNews = async (
  symbol: string,
  params?: { limit?: number; offset?: number }
): Promise<Array<{
  id: string
  title: string
  summary: string
  url: string
  source: string
  published_at: string
  sentiment: 'positive' | 'negative' | 'neutral'
}>> => {
  return api.get(`/stocks/${symbol}/news`, params)
}

// 获取股票公告
export const getStockAnnouncements = async (
  symbol: string,
  params?: { limit?: number; offset?: number }
): Promise<Array<{
  id: string
  title: string
  content: string
  type: string
  published_at: string
  url?: string
}>> => {
  return api.get(`/stocks/${symbol}/announcements`, params)
}

// 获取股票财务数据
export const getStockFinancials = async (
  symbol: string,
  params?: { period?: 'annual' | 'quarterly'; limit?: number }
): Promise<Array<{
  period: string
  revenue: number
  net_income: number
  eps: number
  pe_ratio: number
  pb_ratio: number
  roe: number
  debt_to_equity: number
  current_ratio: number
  gross_margin: number
  operating_margin: number
  net_margin: number
}>> => {
  return api.get(`/stocks/${symbol}/financials`, params)
}

// 获取股票分红信息
export const getStockDividends = async (
  symbol: string,
  params?: { limit?: number }
): Promise<Array<{
  ex_date: string
  record_date: string
  payment_date: string
  amount: number
  yield: number
  type: 'cash' | 'stock'
}>> => {
  return api.get(`/stocks/${symbol}/dividends`, params)
}

// 获取股票拆分信息
export const getStockSplits = async (
  symbol: string,
  params?: { limit?: number }
): Promise<Array<{
  date: string
  ratio: string
  from_factor: number
  to_factor: number
}>> => {
  return api.get(`/stocks/${symbol}/splits`, params)
}

// 获取股票持股信息
export const getStockHolders = async (
  symbol: string,
  type: 'institutional' | 'insider' = 'institutional'
): Promise<Array<{
  name: string
  shares: number
  percentage: number
  value: number
  date: string
}>> => {
  return api.get(`/stocks/${symbol}/holders`, { type })
}

// 获取相关股票
export const getRelatedStocks = async (
  symbol: string,
  limit: number = 10
): Promise<Stock[]> => {
  return api.get(`/stocks/${symbol}/related`, { limit })
}

// 获取股票评级
export const getStockRatings = async (
  symbol: string
): Promise<Array<{
  analyst: string
  rating: 'buy' | 'hold' | 'sell' | 'strong_buy' | 'strong_sell'
  target_price: number
  current_price: number
  date: string
  note?: string
}>> => {
  return api.get(`/stocks/${symbol}/ratings`)
}

// 获取股票期权链
export const getStockOptions = async (
  symbol: string,
  expiration?: string
): Promise<{
  calls: Array<{
    strike: number
    last_price: number
    bid: number
    ask: number
    volume: number
    open_interest: number
    implied_volatility: number
  }>
  puts: Array<{
    strike: number
    last_price: number
    bid: number
    ask: number
    volume: number
    open_interest: number
    implied_volatility: number
  }>
}> => {
  return api.get(`/stocks/${symbol}/options`, { expiration })
}

// 导出所有股票服务
export const stockService = {
  getStockList,
  getStock,
  searchStocks,
  getStockPrice,
  getStockPriceBySymbol,
  getStockHistory,
  getTechnicalIndicators,
  getMarketOverview,
  getHotStocks,
  getGainers,
  getLosers,
  getMostActive,
  getSectors,
  getStocksBySector,
  addToWatchlist,
  removeFromWatchlist,
  getWatchlist,
  getStockNews,
  getStockAnnouncements,
  getStockFinancials,
  getStockDividends,
  getStockSplits,
  getStockHolders,
  getRelatedStocks,
  getStockRatings,
  getStockOptions,
}

export default stockService