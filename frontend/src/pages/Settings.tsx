import React, { useState } from 'react'
import { Card, Form, Input, InputNumber, Select, Switch, Button, Space, Tabs, Alert, Divider } from 'antd'
import { SaveOutlined, ReloadOutlined } from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

import { settingsService } from '@services/settingsService'
import type { SystemSettings, NotificationSettings, TradingSettings } from '@types/index'

const { Option } = Select
const { TabPane } = Tabs
const { TextArea } = Input

const Settings: React.FC = () => {
  const [activeTab, setActiveTab] = useState('system')
  const [systemForm] = Form.useForm()
  const [tradingForm] = Form.useForm()
  const [notificationForm] = Form.useForm()
  
  const queryClient = useQueryClient()

  // 获取系统设置
  const { data: systemSettings, isLoading: isSystemLoading } = useQuery({
    queryKey: ['settings', 'system'],
    queryFn: settingsService.getSystemSettings,
  })

  // 获取交易设置
  const { data: tradingSettings, isLoading: isTradingLoading } = useQuery({
    queryKey: ['settings', 'trading'],
    queryFn: settingsService.getTradingSettings,
  })

  // 获取通知设置
  const { data: notificationSettings, isLoading: isNotificationLoading } = useQuery({
    queryKey: ['settings', 'notification'],
    queryFn: settingsService.getNotificationSettings,
  })

  // 保存系统设置
  const saveSystemMutation = useMutation({
    mutationFn: settingsService.updateSystemSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'system'] })
    },
  })

  // 保存交易设置
  const saveTradingMutation = useMutation({
    mutationFn: settingsService.updateTradingSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'trading'] })
    },
  })

  // 保存通知设置
  const saveNotificationMutation = useMutation({
    mutationFn: settingsService.updateNotificationSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'notification'] })
    },
  })

  const handleSaveSystem = async () => {
    try {
      const values = await systemForm.validateFields()
      saveSystemMutation.mutate(values)
    } catch (error) {
      console.error('系统设置保存失败:', error)
    }
  }

  const handleSaveTrading = async () => {
    try {
      const values = await tradingForm.validateFields()
      saveTradingMutation.mutate(values)
    } catch (error) {
      console.error('交易设置保存失败:', error)
    }
  }

  const handleSaveNotification = async () => {
    try {
      const values = await notificationForm.validateFields()
      saveNotificationMutation.mutate(values)
    } catch (error) {
      console.error('通知设置保存失败:', error)
    }
  }

  const handleReset = () => {
    switch (activeTab) {
      case 'system':
        systemForm.resetFields()
        break
      case 'trading':
        tradingForm.resetFields()
        break
      case 'notification':
        notificationForm.resetFields()
        break
    }
  }

  return (
    <div className="p-6 space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">系统设置</h1>
          <p className="text-gray-600 mt-1">
            配置系统运行参数和个人偏好设置
          </p>
        </div>
      </div>

      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          {/* 系统设置 */}
          <TabPane tab="系统设置" key="system">
            <div className="max-w-2xl">
              <Alert
                message="系统配置"
                description="配置系统的基本运行参数和数据源设置"
                type="info"
                showIcon
                className="mb-6"
              />
              
              <Form
                form={systemForm}
                layout="vertical"
                initialValues={systemSettings}
                onFinish={handleSaveSystem}
              >
                <Divider orientation="left">数据源配置</Divider>
                
                <Form.Item
                  name="data_source"
                  label="主要数据源"
                  rules={[{ required: true, message: '请选择数据源' }]}
                >
                  <Select placeholder="选择数据源">
                    <Option value="tushare">Tushare</Option>
                    <Option value="eastmoney">东方财富</Option>
                    <Option value="sina">新浪财经</Option>
                    <Option value="local">本地CSV</Option>
                  </Select>
                </Form.Item>
                
                <Form.Item
                  name="tushare_token"
                  label="Tushare Token"
                  rules={[{ required: true, message: '请输入Tushare Token' }]}
                >
                  <Input.Password placeholder="输入Tushare API Token" />
                </Form.Item>
                
                <Form.Item
                  name="data_cache_duration"
                  label="数据缓存时长(分钟)"
                  rules={[{ required: true, message: '请输入缓存时长' }]}
                >
                  <InputNumber min={1} max={1440} placeholder="如：30" />
                </Form.Item>
                
                <Divider orientation="left">系统运行</Divider>
                
                <Form.Item
                  name="auto_run_enabled"
                  label="自动运行"
                  valuePropName="checked"
                >
                  <Switch checkedChildren="启用" unCheckedChildren="禁用" />
                </Form.Item>
                
                <Form.Item
                  name="run_schedule"
                  label="运行时间"
                  rules={[{ required: true, message: '请输入运行时间' }]}
                >
                  <Input placeholder="如：14:50 (尾盘推荐时间)" />
                </Form.Item>
                
                <Form.Item
                  name="log_level"
                  label="日志级别"
                  rules={[{ required: true, message: '请选择日志级别' }]}
                >
                  <Select placeholder="选择日志级别">
                    <Option value="DEBUG">DEBUG</Option>
                    <Option value="INFO">INFO</Option>
                    <Option value="WARNING">WARNING</Option>
                    <Option value="ERROR">ERROR</Option>
                  </Select>
                </Form.Item>
                
                <Form.Item>
                  <Space>
                    <Button 
                      type="primary" 
                      icon={<SaveOutlined />} 
                      htmlType="submit"
                      loading={saveSystemMutation.isPending}
                    >
                      保存设置
                    </Button>
                    <Button icon={<ReloadOutlined />} onClick={handleReset}>
                      重置
                    </Button>
                  </Space>
                </Form.Item>
              </Form>
            </div>
          </TabPane>

          {/* 交易设置 */}
          <TabPane tab="交易设置" key="trading">
            <div className="max-w-2xl">
              <Alert
                message="交易参数"
                description="配置策略运行和风险控制相关参数"
                type="info"
                showIcon
                className="mb-6"
              />
              
              <Form
                form={tradingForm}
                layout="vertical"
                initialValues={tradingSettings}
                onFinish={handleSaveTrading}
              >
                <Divider orientation="left">基础参数</Divider>
                
                <Form.Item
                  name="initial_capital"
                  label="初始资金(万元)"
                  rules={[{ required: true, message: '请输入初始资金' }]}
                >
                  <InputNumber min={1} max={10000} placeholder="如：100" />
                </Form.Item>
                
                <Form.Item
                  name="max_position_ratio"
                  label="单只股票最大仓位比例(%)"
                  rules={[{ required: true, message: '请输入最大仓位比例' }]}
                >
                  <InputNumber min={1} max={100} placeholder="如：10" />
                </Form.Item>
                
                <Form.Item
                  name="max_total_positions"
                  label="最大持仓股票数"
                  rules={[{ required: true, message: '请输入最大持仓数' }]}
                >
                  <InputNumber min={1} max={50} placeholder="如：10" />
                </Form.Item>
                
                <Divider orientation="left">风险控制</Divider>
                
                <Form.Item
                  name="stop_loss_ratio"
                  label="止损比例(%)"
                  rules={[{ required: true, message: '请输入止损比例' }]}
                >
                  <InputNumber min={1} max={50} step={0.1} placeholder="如：5" />
                </Form.Item>
                
                <Form.Item
                  name="take_profit_ratio"
                  label="止盈比例(%)"
                  rules={[{ required: true, message: '请输入止盈比例' }]}
                >
                  <InputNumber min={1} max={100} step={0.1} placeholder="如：15" />
                </Form.Item>
                
                <Form.Item
                  name="max_drawdown_limit"
                  label="最大回撤限制(%)"
                  rules={[{ required: true, message: '请输入最大回撤限制' }]}
                >
                  <InputNumber min={1} max={50} step={0.1} placeholder="如：10" />
                </Form.Item>
                
                <Divider orientation="left">筛选条件</Divider>
                
                <Form.Item
                  name="min_market_cap"
                  label="最小市值(亿元)"
                  rules={[{ required: true, message: '请输入最小市值' }]}
                >
                  <InputNumber min={1} max={10000} placeholder="如：50" />
                </Form.Item>
                
                <Form.Item
                  name="max_pe_ratio"
                  label="最大市盈率"
                  rules={[{ required: true, message: '请输入最大市盈率' }]}
                >
                  <InputNumber min={1} max={200} placeholder="如：50" />
                </Form.Item>
                
                <Form.Item
                  name="exclude_st_stocks"
                  label="排除ST股票"
                  valuePropName="checked"
                >
                  <Switch checkedChildren="是" unCheckedChildren="否" />
                </Form.Item>
                
                <Form.Item>
                  <Space>
                    <Button 
                      type="primary" 
                      icon={<SaveOutlined />} 
                      htmlType="submit"
                      loading={saveTradingMutation.isPending}
                    >
                      保存设置
                    </Button>
                    <Button icon={<ReloadOutlined />} onClick={handleReset}>
                      重置
                    </Button>
                  </Space>
                </Form.Item>
              </Form>
            </div>
          </TabPane>

          {/* 通知设置 */}
          <TabPane tab="通知设置" key="notification">
            <div className="max-w-2xl">
              <Alert
                message="通知配置"
                description="配置推荐结果和系统状态的通知方式"
                type="info"
                showIcon
                className="mb-6"
              />
              
              <Form
                form={notificationForm}
                layout="vertical"
                initialValues={notificationSettings}
                onFinish={handleSaveNotification}
              >
                <Divider orientation="left">邮件通知</Divider>
                
                <Form.Item
                  name="email_enabled"
                  label="启用邮件通知"
                  valuePropName="checked"
                >
                  <Switch checkedChildren="启用" unCheckedChildren="禁用" />
                </Form.Item>
                
                <Form.Item
                  name="email_address"
                  label="邮箱地址"
                  rules={[
                    { required: true, message: '请输入邮箱地址' },
                    { type: 'email', message: '请输入有效的邮箱地址' }
                  ]}
                >
                  <Input placeholder="输入接收通知的邮箱地址" />
                </Form.Item>
                
                <Form.Item
                  name="email_smtp_server"
                  label="SMTP服务器"
                  rules={[{ required: true, message: '请输入SMTP服务器' }]}
                >
                  <Input placeholder="如：smtp.qq.com" />
                </Form.Item>
                
                <Form.Item
                  name="email_smtp_port"
                  label="SMTP端口"
                  rules={[{ required: true, message: '请输入SMTP端口' }]}
                >
                  <InputNumber min={1} max={65535} placeholder="如：587" />
                </Form.Item>
                
                <Divider orientation="left">微信通知</Divider>
                
                <Form.Item
                  name="wechat_enabled"
                  label="启用微信通知"
                  valuePropName="checked"
                >
                  <Switch checkedChildren="启用" unCheckedChildren="禁用" />
                </Form.Item>
                
                <Form.Item
                  name="wechat_webhook"
                  label="微信机器人Webhook"
                  rules={[{ required: true, message: '请输入Webhook地址' }]}
                >
                  <TextArea 
                    rows={3} 
                    placeholder="输入企业微信或钉钉机器人的Webhook地址" 
                  />
                </Form.Item>
                
                <Divider orientation="left">通知内容</Divider>
                
                <Form.Item
                  name="notify_buy_recommendations"
                  label="买入推荐通知"
                  valuePropName="checked"
                >
                  <Switch checkedChildren="启用" unCheckedChildren="禁用" />
                </Form.Item>
                
                <Form.Item
                  name="notify_sell_recommendations"
                  label="卖出推荐通知"
                  valuePropName="checked"
                >
                  <Switch checkedChildren="启用" unCheckedChildren="禁用" />
                </Form.Item>
                
                <Form.Item
                  name="notify_system_errors"
                  label="系统错误通知"
                  valuePropName="checked"
                >
                  <Switch checkedChildren="启用" unCheckedChildren="禁用" />
                </Form.Item>
                
                <Form.Item
                  name="notify_strategy_alerts"
                  label="策略预警通知"
                  valuePropName="checked"
                >
                  <Switch checkedChildren="启用" unCheckedChildren="禁用" />
                </Form.Item>
                
                <Form.Item>
                  <Space>
                    <Button 
                      type="primary" 
                      icon={<SaveOutlined />} 
                      htmlType="submit"
                      loading={saveNotificationMutation.isPending}
                    >
                      保存设置
                    </Button>
                    <Button icon={<ReloadOutlined />} onClick={handleReset}>
                      重置
                    </Button>
                  </Space>
                </Form.Item>
              </Form>
            </div>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  )
}

export default Settings