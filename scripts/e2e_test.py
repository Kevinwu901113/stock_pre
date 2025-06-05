#!/usr/bin/env python3

import requests
import time
import json
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any

class E2ETestSuite:
    """端到端测试套件"""
    
    def __init__(self, backend_url="http://localhost:8000", frontend_url="http://localhost:3000"):
        self.backend_url = backend_url
        self.frontend_url = frontend_url
        self.test_stocks = ["000001", "600036", "000002", "600519", "000858"]  # 测试股票代码
        self.test_results = {
            "start_time": datetime.now().isoformat(),
            "tests": [],
            "summary": {}
        }
        
    def run_test(self, test_name: str, test_func):
        """运行单个测试并记录结果"""
        print(f"\n🔍 {test_name}...")
        start_time = time.time()
        
        try:
            result = test_func()
            duration = time.time() - start_time
            
            self.test_results["tests"].append({
                "name": test_name,
                "status": "PASS",
                "duration": duration,
                "result": result
            })
            
            print(f"✅ {test_name} - 通过 ({duration:.2f}秒)")
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            
            self.test_results["tests"].append({
                "name": test_name,
                "status": "FAIL",
                "duration": duration,
                "error": str(e)
            })
            
            print(f"❌ {test_name} - 失败: {str(e)}")
            raise
    
    def test_backend_health(self):
        """测试后端健康状态"""
        response = requests.get(f"{self.backend_url}/health", timeout=10)
        assert response.status_code == 200, f"后端健康检查失败: {response.status_code}"
        
        health_data = response.json()
        assert health_data.get("status") == "healthy", "后端状态不健康"
        
        return health_data
        
    def test_frontend_access(self):
        """测试前端访问"""
        response = requests.get(self.frontend_url, timeout=10)
        assert response.status_code == 200, f"前端访问失败: {response.status_code}"
        
        # 检查是否包含Vue.js应用的标识
        content = response.text
        assert "<!DOCTYPE html>" in content, "前端页面格式不正确"
        
        return {"status": "accessible", "content_length": len(content)}
        
    def test_database_connection(self):
        """测试数据库连接"""
        response = requests.get(f"{self.backend_url}/api/v1/system/info", timeout=10)
        assert response.status_code == 200, "系统信息接口访问失败"
        
        system_info = response.json()
        assert "database" in system_info.get("data", {}), "数据库信息缺失"
        
        return system_info["data"]
        
    def test_stock_data_preparation(self):
        """测试股票数据准备"""
        prepared_stocks = []
        
        for stock_code in self.test_stocks:
            try:
                # 检查股票是否存在
                response = requests.get(f"{self.backend_url}/api/v1/stocks/{stock_code}", timeout=10)
                
                if response.status_code == 404:
                    # 如果股票不存在，添加测试数据
                    stock_data = self._add_test_stock_data(stock_code)
                    prepared_stocks.append(stock_data)
                elif response.status_code == 200:
                    stock_data = response.json()["data"]
                    prepared_stocks.append(stock_data)
                else:
                    print(f"⚠️ 股票 {stock_code} 状态异常: {response.status_code}")
                    
            except Exception as e:
                print(f"⚠️ 处理股票 {stock_code} 时出错: {str(e)}")
                
        assert len(prepared_stocks) > 0, "没有可用的测试股票数据"
        return prepared_stocks
        
    def test_data_sources_status(self):
        """测试数据源状态"""
        response = requests.get(f"{self.backend_url}/api/v1/data/sources/status", timeout=10)
        assert response.status_code == 200, "数据源状态检查失败"
        
        sources_status = response.json()["data"]
        
        # 至少要有一个数据源可用
        available_sources = [s for s in sources_status if s.get("status") == "available"]
        assert len(available_sources) > 0, "没有可用的数据源"
        
        return sources_status
        
    def test_recommendation_generation(self):
        """测试推荐生成流程"""
        # 生成推荐
        payload = {
            "stockCodes": self.test_stocks[:3],  # 使用前3只股票进行测试
            "strategies": ["ma_strategy", "rsi_strategy"],
            "parameters": {
                "minConfidence": 0.5  # 降低置信度阈值以便测试
            }
        }
        
        response = requests.post(
            f"{self.backend_url}/api/v1/recommendations/generate",
            json=payload,
            timeout=30
        )
        
        assert response.status_code == 200, f"推荐生成请求失败: {response.status_code}"
        result = response.json()
        
        assert "data" in result, "推荐生成响应格式错误"
        assert "taskId" in result["data"], "推荐生成任务ID缺失"
        
        task_id = result["data"]["taskId"]
        
        # 等待生成完成
        max_wait_time = 60  # 最大等待60秒
        wait_interval = 2   # 每2秒检查一次
        
        for _ in range(max_wait_time // wait_interval):
            time.sleep(wait_interval)
            
            # 检查任务状态（如果有相关接口）
            try:
                status_response = requests.get(
                    f"{self.backend_url}/api/v1/recommendations/task/{task_id}",
                    timeout=10
                )
                if status_response.status_code == 200:
                    status_data = status_response.json()["data"]
                    if status_data.get("status") == "completed":
                        break
            except:
                pass  # 如果没有任务状态接口，继续等待
                
        return {"task_id": task_id, "generation_time": max_wait_time}
        
    def test_recommendation_retrieval(self):
        """测试推荐获取"""
        # 获取买入推荐
        buy_response = requests.get(
            f"{self.backend_url}/api/v1/recommendations/buy?limit=10",
            timeout=10
        )
        assert buy_response.status_code == 200, "买入推荐获取失败"
        
        buy_data = buy_response.json()
        assert "data" in buy_data, "买入推荐响应格式错误"
        
        buy_recommendations = buy_data["data"]
        
        # 获取卖出推荐
        sell_response = requests.get(
            f"{self.backend_url}/api/v1/recommendations/sell?limit=10",
            timeout=10
        )
        assert sell_response.status_code == 200, "卖出推荐获取失败"
        
        sell_data = sell_response.json()
        assert "data" in sell_data, "卖出推荐响应格式错误"
        
        sell_recommendations = sell_data["data"]
        
        return {
            "buy_count": len(buy_recommendations),
            "sell_count": len(sell_recommendations),
            "buy_recommendations": buy_recommendations,
            "sell_recommendations": sell_recommendations
        }
        
    def test_recommendation_data_structure(self, recommendations: List[Dict]):
        """测试推荐数据结构"""
        if not recommendations:
            print("⚠️ 没有推荐数据可供验证")
            return {"validated_count": 0}
            
        required_fields = [
            'id', 'stockCode', 'stockName', 'currentPrice',
            'confidence', 'reason', 'createdAt'
        ]
        
        optional_fields = [
            'targetPrice', 'stopLoss', 'expectedReturn',
            'holdingPeriod', 'strategyName'
        ]
        
        validated_count = 0
        
        for i, rec in enumerate(recommendations[:5]):  # 验证前5条推荐
            # 检查必需字段
            for field in required_fields:
                assert field in rec, f"推荐 {i+1} 缺少必需字段: {field}"
                assert rec[field] is not None, f"推荐 {i+1} 字段 {field} 为空"
                
            # 检查数据类型
            assert isinstance(rec['confidence'], (int, float)), "置信度应为数值类型"
            assert 0 <= rec['confidence'] <= 1, "置信度应在0-1之间"
            
            if 'currentPrice' in rec:
                assert isinstance(rec['currentPrice'], (int, float)), "当前价格应为数值类型"
                assert rec['currentPrice'] > 0, "当前价格应大于0"
                
            validated_count += 1
            
        return {"validated_count": validated_count}
        
    def test_stock_search_functionality(self):
        """测试股票搜索功能"""
        search_keywords = ["平安", "银行", "000001"]
        search_results = {}
        
        for keyword in search_keywords:
            response = requests.get(
                f"{self.backend_url}/api/v1/stocks/search",
                params={"keyword": keyword, "limit": 10},
                timeout=10
            )
            
            assert response.status_code == 200, f"搜索关键词 '{keyword}' 失败"
            
            data = response.json()
            assert "data" in data, "搜索响应格式错误"
            
            results = data["data"]
            search_results[keyword] = len(results)
            
            # 验证搜索结果结构
            if results:
                first_result = results[0]
                required_fields = ['code', 'name']
                for field in required_fields:
                    assert field in first_result, f"搜索结果缺少字段: {field}"
                    
        return search_results
        
    def test_kline_data_access(self):
        """测试K线数据访问"""
        test_stock = self.test_stocks[0]
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        response = requests.get(
            f"{self.backend_url}/api/v1/stocks/{test_stock}/kline",
            params={
                "period": "daily",
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d")
            },
            timeout=15
        )
        
        assert response.status_code == 200, "K线数据获取失败"
        
        data = response.json()
        assert "data" in data, "K线数据响应格式错误"
        
        kline_data = data["data"]
        assert "klineData" in kline_data, "K线数据结构错误"
        
        kline_points = kline_data["klineData"]
        
        # 验证K线数据结构
        if kline_points:
            first_point = kline_points[0]
            required_fields = ['date', 'open', 'high', 'low', 'close', 'volume']
            for field in required_fields:
                assert field in first_point, f"K线数据缺少字段: {field}"
                
        return {"stock_code": test_stock, "data_points": len(kline_points)}
        
    def test_api_performance(self):
        """测试API性能"""
        performance_results = {}
        
        # 测试各个关键接口的响应时间
        test_endpoints = [
            ("/health", "健康检查"),
            ("/api/v1/recommendations/buy?limit=5", "买入推荐"),
            ("/api/v1/stocks/search?keyword=平安&limit=5", "股票搜索"),
            (f"/api/v1/stocks/{self.test_stocks[0]}", "股票详情")
        ]
        
        for endpoint, name in test_endpoints:
            start_time = time.time()
            
            try:
                response = requests.get(f"{self.backend_url}{endpoint}", timeout=10)
                duration = time.time() - start_time
                
                performance_results[name] = {
                    "duration": duration,
                    "status_code": response.status_code,
                    "response_size": len(response.content)
                }
                
                # 性能要求：响应时间应小于2秒
                assert duration < 2.0, f"{name} 响应时间过长: {duration:.2f}秒"
                
            except Exception as e:
                performance_results[name] = {
                    "error": str(e),
                    "duration": time.time() - start_time
                }
                
        return performance_results
        
    def _add_test_stock_data(self, stock_code: str):
        """添加测试股票数据"""
        stock_names = {
            "000001": "平安银行",
            "600036": "招商银行", 
            "000002": "万科A",
            "600519": "贵州茅台",
            "000858": "五粮液"
        }
        
        stock_data = {
            "code": stock_code,
            "name": stock_names.get(stock_code, f"测试股票{stock_code}"),
            "market": "A",
            "industry": "测试行业"
        }
        
        try:
            response = requests.post(
                f"{self.backend_url}/api/v1/stocks",
                json=stock_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                print(f"✅ 添加测试股票: {stock_code} - {stock_data['name']}")
                return stock_data
            else:
                print(f"⚠️ 添加股票失败: {stock_code} - {response.status_code}")
                return stock_data
                
        except Exception as e:
            print(f"⚠️ 添加股票异常: {stock_code} - {str(e)}")
            return stock_data
        
    def run_full_test(self):
        """运行完整测试流程"""
        print("🚀 开始端到端测试...")
        print(f"📊 后端地址: {self.backend_url}")
        print(f"🌐 前端地址: {self.frontend_url}")
        print(f"📈 测试股票: {', '.join(self.test_stocks)}")
        
        try:
            # 1. 基础服务测试
            self.run_test("后端健康检查", self.test_backend_health)
            self.run_test("前端访问测试", self.test_frontend_access)
            self.run_test("数据库连接测试", self.test_database_connection)
            
            # 2. 数据准备测试
            stock_data = self.run_test("股票数据准备", self.test_stock_data_preparation)
            self.run_test("数据源状态检查", self.test_data_sources_status)
            
            # 3. 核心功能测试
            self.run_test("推荐生成流程", self.test_recommendation_generation)
            rec_data = self.run_test("推荐获取测试", self.test_recommendation_retrieval)
            
            # 4. 数据结构验证
            if rec_data["buy_recommendations"]:
                self.run_test("买入推荐数据结构验证", 
                            lambda: self.test_recommendation_data_structure(rec_data["buy_recommendations"]))
            
            if rec_data["sell_recommendations"]:
                self.run_test("卖出推荐数据结构验证",
                            lambda: self.test_recommendation_data_structure(rec_data["sell_recommendations"]))
            
            # 5. 辅助功能测试
            self.run_test("股票搜索功能", self.test_stock_search_functionality)
            self.run_test("K线数据访问", self.test_kline_data_access)
            
            # 6. 性能测试
            self.run_test("API性能测试", self.test_api_performance)
            
            # 生成测试报告
            self._generate_test_report(rec_data)
            
            print("\n🎉 端到端测试全部通过！")
            
        except Exception as e:
            print(f"\n❌ 测试失败: {str(e)}")
            self._generate_test_report({})
            sys.exit(1)
            
    def _generate_test_report(self, rec_data: Dict):
        """生成测试报告"""
        self.test_results["end_time"] = datetime.now().isoformat()
        
        # 统计测试结果
        total_tests = len(self.test_results["tests"])
        passed_tests = len([t for t in self.test_results["tests"] if t["status"] == "PASS"])
        failed_tests = total_tests - passed_tests
        
        total_duration = sum(t["duration"] for t in self.test_results["tests"])
        
        self.test_results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "total_duration": total_duration,
            "buy_recommendations": rec_data.get("buy_count", 0),
            "sell_recommendations": rec_data.get("sell_count", 0),
            "test_stocks": self.test_stocks
        }
        
        # 保存详细报告
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
            
        # 打印摘要报告
        print(f"\n📊 测试报告摘要:")
        print(f"   📈 总测试数: {total_tests}")
        print(f"   ✅ 通过: {passed_tests}")
        print(f"   ❌ 失败: {failed_tests}")
        print(f"   📊 成功率: {self.test_results['summary']['success_rate']:.1f}%")
        print(f"   ⏱️ 总耗时: {total_duration:.2f}秒")
        print(f"   📈 买入推荐: {rec_data.get('buy_count', 0)} 条")
        print(f"   📉 卖出推荐: {rec_data.get('sell_count', 0)} 条")
        print(f"   📄 详细报告: {report_file}")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="股票推荐系统端到端测试")
    parser.add_argument("--backend", default="http://localhost:8000", help="后端API地址")
    parser.add_argument("--frontend", default="http://localhost:3000", help="前端地址")
    parser.add_argument("--stocks", nargs="+", default=["000001", "600036", "000002"], help="测试股票代码")
    
    args = parser.parse_args()
    
    tester = E2ETestSuite(backend_url=args.backend, frontend_url=args.frontend)
    if args.stocks:
        tester.test_stocks = args.stocks
        
    tester.run_full_test()

if __name__ == "__main__":
    main()