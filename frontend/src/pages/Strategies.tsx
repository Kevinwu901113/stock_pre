import React, { useState } from 'react'
import { Card, Table, Switch, Button, Space, Modal, Form, InputNumber, Select, Tag, Tooltip, Alert, Tabs } from 'antd'
import { SettingOutlined, PlayCircleOutlined, PauseCircleOutlined, EditOutlined, EyeOutlined } from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import type { ColumnsType } from 'antd/es/table'

import { strategyService } from '@services/strategyService'
import type { Strategy, StrategyConfig, StrategyBacktest } from '@types/index'

const { Option } = Select
const { TabPane } = Tabs

interface StrategyConfigModalProps {
  visible: boolean
  strategy: Strategy | null
  onClose: () => void
  onSave: (config: StrategyConfig) => void
}

const StrategyConfigModal: React.FC<StrategyConfigModalProps> = ({
  visible,
  strategy,
  onClose,
  onSave
}) => {
  const [form] = Form.useForm()

  const handleSave = async () => {
    try {
      const values = await form.validateFields()
      onSave(values)
      onClose()
    } catch (error) {
      console.error('表单验证失败:', error)
    }
  }

  const renderConfigFields = () => {
    if (!strategy) return null

    switch (strategy.type) {
      case 'ma_breakout':
        return (
          <>
            <Form.Item
              name="short_period"
              label="短期均线周期"
              rules={[{ required: true, message: '请输入短期均线周期' }]}
            >
              <InputNumber min={1} max={100} placeholder="如：5" />
            </Form.Item>
            <Form.Item
              name="long_period"
              label="长期均线周期"
              rules={[{ required: true, message: '请输入长期均线周期' }]}
            >
              <InputNumber min={1} max={200} placeholder="如：20" />
            </Form.Item>
            <Form.Item
              name="volume_threshold"
              label="成交量阈值"
              rules={[{ required: true, message: '请输入成交量阈值' }]}
            >
              <InputNumber min={0} step={0.1} placeholder="如：1.5" />
            </Form.Item>
          </>
        )
      case 'momentum':
        return (
          <>
            <Form.Item
              name="lookback_period"
              label="回看周期"
              rules={[{ required: true, message: '请输入回看周期' }]}
            >
              <InputNumber min={1} max={50} placeholder="如：10" />
            </Form.Item>
            <Form.Item
              name="momentum_threshold"
              label="动量阈值"
              rules={[{ required: true, message: '请输入动量阈值' }]}
            >
              <InputNumber min={0} step={0.01} placeholder="如：0.05" />
            </Form.Item>
            <Form.Item
              name="min_volume"
              label="最小成交量"
              rules={[{ required: true, message: '请输入最小成交量' }]}
            >
              <InputNumber min={0} placeholder="如：1000000" />
            </Form.Item>
          </>
        )
      default:
        return (
          <Alert
            message="暂不支持该策略的参数配置"
            type="warning"
            showIcon
          />
        )
    }
  }

  return (
    <Modal
      title={`配置策略: ${strategy?.name}`}
      open={visible}
      onCancel={onClose}
      onOk={handleSave}
      width={600}
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={strategy?.config}
      >
        <Form.Item
          name="enabled"
          label="启用状态"
          valuePropName="checked"
        >
          <Switch checkedChildren="启用" unCheckedChildren="禁用" />
        </Form.Item>
        
        <Form.Item
          name="priority"
          label="优先级"
          rules={[{ required: true, message: '请选择优先级' }]}
        >
          <Select placeholder="选择优先级">
            <Option value="high">高</Option>
            <Option value="medium">中</Option>
            <Option value="low">低</Option>
          </Select>
        </Form.Item>
        
        <Form.Item
          name="max_positions"
          label="最大持仓数"
          rules={[{ required: true, message: '请输入最大持仓数' }]}
        >
          <InputNumber min={1} max={50} placeholder="如：10" />
        </Form.Item>
        
        {renderConfigFields()}
        
        <Form.Item
          name="risk_level"
          label="风险等级"
          rules={[{ required: true, message: '请选择风险等级' }]}
        >
          <Select placeholder="选择风险等级">
            <Option value="low">低风险</Option>
            <Option value="medium">中风险</Option>
            <Option value="high">高风险</Option>
          </Select>
        </Form.Item>
      </Form>
    </Modal>
  )
}

const Strategies: React.FC = () => {
  const [configModalVisible, setConfigModalVisible] = useState(false)
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null)
  const [backtestModalVisible, setBacktestModalVisible] = useState(false)
  const [activeTab, setActiveTab] = useState('list')
  
  const queryClient = useQueryClient()

  // 获取策略列表
  const { data: strategies, isLoading } = useQuery({
    queryKey: ['strategies'],
    queryFn: strategyService.getStrategies,
  })

  // 获取策略回测结果
  const { data: backtestResults } = useQuery({
    queryKey: ['strategies', 'backtest'],
    queryFn: strategyService.getBacktestResults,
  })

  // 更新策略状态
  const updateStrategyMutation = useMutation({
    mutationFn: ({ id, enabled }: { id: string; enabled: boolean }) =>
      strategyService.updateStrategy(id, { enabled }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['strategies'] })
    },
  })

  // 保存策略配置
  const saveConfigMutation = useMutation({
    mutationFn: ({ id, config }: { id: string; config: StrategyConfig }) =>
      strategyService.updateStrategyConfig(id, config),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['strategies'] })
    },
  })

  // 策略列表表格列定义
  const columns: ColumnsType<Strategy> = [
    {
      title: '策略名称',
      dataIndex: 'name',
      key: 'name',
      width: 150,
      render: (name: string, record: Strategy) => (
        <div>
          <div className="font-medium">{name}</div>
          <div className="text-sm text-gray-500">{record.description}</div>
        </div>
      ),
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 120,
      render: (type: string) => {
        const typeMap: Record<string, { label: string; color: string }> = {
          ma_breakout: { label: '均线突破', color: 'blue' },
          momentum: { label: '动量策略', color: 'green' },
          mean_reversion: { label: '均值回归', color: 'orange' },
          volume_price: { label: '量价策略', color: 'purple' },
        }
        const config = typeMap[type] || { label: type, color: 'default' }
        return <Tag color={config.color}>{config.label}</Tag>
      },
    },
    {
      title: '状态',
      dataIndex: 'enabled',
      key: 'enabled',
      width: 100,
      render: (enabled: boolean, record: Strategy) => (
        <Switch
          checked={enabled}
          onChange={(checked) => 
            updateStrategyMutation.mutate({ id: record.id, enabled: checked })
          }
          loading={updateStrategyMutation.isPending}
          checkedChildren="启用"
          unCheckedChildren="禁用"
        />
      ),
    },
    {
      title: '优先级',
      dataIndex: ['config', 'priority'],
      key: 'priority',
      width: 100,
      render: (priority: string) => {
        const colors = {
          high: 'red',
          medium: 'orange',
          low: 'green',
        }
        const labels = {
          high: '高',
          medium: '中',
          low: '低',
        }
        return <Tag color={colors[priority as keyof typeof colors]}>{labels[priority as keyof typeof labels]}</Tag>
      },
    },
    {
      title: '风险等级',
      dataIndex: ['config', 'risk_level'],
      key: 'risk_level',
      width: 100,
      render: (level: string) => {
        const colors = {
          low: 'green',
          medium: 'orange',
          high: 'red',
        }
        const labels = {
          low: '低风险',
          medium: '中风险',
          high: '高风险',
        }
        return <Tag color={colors[level as keyof typeof colors]}>{labels[level as keyof typeof labels]}</Tag>
      },
    },
    {
      title: '最大持仓',
      dataIndex: ['config', 'max_positions'],
      key: 'max_positions',
      width: 100,
      align: 'center',
      render: (positions: number) => `${positions}个`,
    },
    {
      title: '最近运行',
      dataIndex: 'last_run',
      key: 'last_run',
      width: 120,
      render: (time: string) => time ? new Date(time).toLocaleString() : '-',
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      render: (_, record: Strategy) => (
        <Space size="small">
          <Tooltip title="配置参数">
            <Button
              type="text"
              icon={<SettingOutlined />}
              size="small"
              onClick={() => handleConfig(record)}
            />
          </Tooltip>
          <Tooltip title="查看详情">
            <Button
              type="text"
              icon={<EyeOutlined />}
              size="small"
              onClick={() => handleViewDetails(record)}
            />
          </Tooltip>
          <Tooltip title={record.enabled ? '暂停策略' : '启动策略'}>
            <Button
              type="text"
              icon={record.enabled ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
              size="small"
              onClick={() => 
                updateStrategyMutation.mutate({ id: record.id, enabled: !record.enabled })
              }
            />
          </Tooltip>
        </Space>
      ),
    },
  ]

  // 回测结果表格列定义
  const backtestColumns: ColumnsType<StrategyBacktest> = [
    {
      title: '策略名称',
      dataIndex: 'strategy_name',
      key: 'strategy_name',
      width: 150,
    },
    {
      title: '回测期间',
      dataIndex: 'period',
      key: 'period',
      width: 150,
      render: (period: { start: string; end: string }) => 
        `${period.start} ~ ${period.end}`,
    },
    {
      title: '总收益率',
      dataIndex: 'total_return',
      key: 'total_return',
      width: 100,
      render: (rate: number) => (
        <span className={rate >= 0 ? 'text-green-600' : 'text-red-600'}>
          {rate >= 0 ? '+' : ''}{rate.toFixed(2)}%
        </span>
      ),
    },
    {
      title: '年化收益',
      dataIndex: 'annual_return',
      key: 'annual_return',
      width: 100,
      render: (rate: number) => (
        <span className={rate >= 0 ? 'text-green-600' : 'text-red-600'}>
          {rate >= 0 ? '+' : ''}{rate.toFixed(2)}%
        </span>
      ),
    },
    {
      title: '最大回撤',
      dataIndex: 'max_drawdown',
      key: 'max_drawdown',
      width: 100,
      render: (rate: number) => (
        <span className="text-red-600">{rate.toFixed(2)}%</span>
      ),
    },
    {
      title: '胜率',
      dataIndex: 'win_rate',
      key: 'win_rate',
      width: 80,
      render: (rate: number) => `${rate.toFixed(1)}%`,
    },
    {
      title: '夏普比率',
      dataIndex: 'sharpe_ratio',
      key: 'sharpe_ratio',
      width: 100,
      render: (ratio: number) => ratio.toFixed(2),
    },
  ]

  const handleConfig = (strategy: Strategy) => {
    setSelectedStrategy(strategy)
    setConfigModalVisible(true)
  }

  const handleViewDetails = (strategy: Strategy) => {
    // TODO: 打开策略详情页面
    console.log('查看策略详情:', strategy)
  }

  const handleSaveConfig = (config: StrategyConfig) => {
    if (selectedStrategy) {
      saveConfigMutation.mutate({ id: selectedStrategy.id, config })
    }
  }

  const handleRunBacktest = () => {
    // TODO: 运行回测
    console.log('运行回测')
  }

  return (
    <div className="p-6 space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">策略管理</h1>
          <p className="text-gray-600 mt-1">
            管理量化策略的配置参数和运行状态
          </p>
        </div>
        <Space>
          <Button type="primary" onClick={handleRunBacktest}>
            运行回测
          </Button>
        </Space>
      </div>

      {/* 策略概览 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {strategies?.data?.length || 0}
            </div>
            <div className="text-sm text-gray-600">总策略数</div>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {strategies?.data?.filter(s => s.enabled).length || 0}
            </div>
            <div className="text-sm text-gray-600">启用策略</div>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">
              {strategies?.data?.filter(s => s.config?.priority === 'high').length || 0}
            </div>
            <div className="text-sm text-gray-600">高优先级</div>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">
              {strategies?.data?.reduce((sum, s) => sum + (s.config?.max_positions || 0), 0) || 0}
            </div>
            <div className="text-sm text-gray-600">总持仓限制</div>
          </div>
        </Card>
      </div>

      {/* 主要内容 */}
      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab="策略列表" key="list">
            <Table
              columns={columns}
              dataSource={strategies?.data || []}
              loading={isLoading}
              rowKey="id"
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
              }}
            />
          </TabPane>
          
          <TabPane tab="回测结果" key="backtest">
            <div className="space-y-4">
              <Alert
                message="策略回测结果"
                description="展示各策略的历史回测表现，帮助评估策略效果"
                type="info"
                showIcon
              />
              
              <Table
                columns={backtestColumns}
                dataSource={backtestResults?.data || []}
                rowKey={(record) => `${record.strategy_name}-${record.period.start}`}
                pagination={false}
              />
            </div>
          </TabPane>
        </Tabs>
      </Card>

      {/* 策略配置弹窗 */}
      <StrategyConfigModal
        visible={configModalVisible}
        strategy={selectedStrategy}
        onClose={() => {
          setConfigModalVisible(false)
          setSelectedStrategy(null)
        }}
        onSave={handleSaveConfig}
      />
    </div>
  )
}

export default Strategies