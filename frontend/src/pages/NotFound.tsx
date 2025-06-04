import React from 'react'
import { Result, Button } from 'antd'
import { useNavigate } from 'react-router-dom'
import { HomeOutlined, ArrowLeftOutlined } from '@ant-design/icons'

const NotFound: React.FC = () => {
  const navigate = useNavigate()

  const handleGoHome = () => {
    navigate('/')
  }

  const handleGoBack = () => {
    navigate(-1)
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <Result
        status="404"
        title="404"
        subTitle="抱歉，您访问的页面不存在。"
        extra={
          <div className="space-x-4">
            <Button type="primary" icon={<HomeOutlined />} onClick={handleGoHome}>
              返回首页
            </Button>
            <Button icon={<ArrowLeftOutlined />} onClick={handleGoBack}>
              返回上页
            </Button>
          </div>
        }
      />
    </div>
  )
}

export default NotFound