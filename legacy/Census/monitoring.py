#!/usr/bin/env python3
"""
CENSUS Monitoring and Observability
=================================

Comprehensive monitoring, health checks, and observability
for the CENSUS system with structured logging and metrics.
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import psutil
import asyncpg

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s", "service": "census-monitoring"}',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """System performance metrics."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    active_connections: int
    database_pool_size: int
    database_connections: int
    sync_operations: Dict[str, int] = None

@dataclass
class HealthCheck:
    """Health check result."""
    service_name: str
    status: str  # healthy, degraded, unhealthy
    message: str
    timestamp: datetime
    response_time_ms: Optional[float] = None
    details: Dict[str, Any] = None

class CENUSMonitoring:
    """
    Comprehensive monitoring and observability for CENSUS system.
    
    Features:
    - System resource monitoring
    - Database health checks
    - Service dependency monitoring
    - Structured logging with JSON output
    - Performance metrics collection
    - Alert threshold monitoring
    """
    
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.db_pool = None
        self.health_checks: Dict[str, HealthCheck] = {}
        self.alert_thresholds = {
            'cpu_warning': 70.0,
            'cpu_critical': 90.0,
            'memory_warning': 80.0,
            'memory_critical': 95.0,
            'disk_warning': 80.0,
            'disk_critical': 95.0,
            'db_connections_warning': 15,
            'db_connections_critical': 25
        }
    
    async def initialize(self):
        """Initialize monitoring system."""
        try:
            self.db_pool = await asyncpg.create_pool(
                self.db_url,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            logger.info("CENSUS Monitoring initialized")
        except Exception as e:
            logger.error(f"Failed to initialize monitoring: {e}")
            raise
    
    async def collect_system_metrics(self) -> SystemMetrics:
        """Collect system performance metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_usage_percent = disk.percent
            
            # Database metrics
            db_connections = 0
            if self.db_pool:
                db_connections = len(self.db_pool._conns)
            
            # Sync operations (would come from sync engine)
            sync_operations = {
                'phone_sync': 0,
                'user_sync': 0,
                'line_sync': 0
            }
            
            return SystemMetrics(
                timestamp=datetime.utcnow(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_usage_percent=disk_usage_percent,
                active_connections=len(psutil.net_connections()),
                database_pool_size=len(self.db_pool._conns) if self.db_pool else 0,
                database_connections=db_connections,
                sync_operations=sync_operations
            )
            
        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
            raise
    
    async def check_database_health(self) -> HealthCheck:
        """Check database connectivity and performance."""
        try:
            start_time = datetime.utcnow()
            
            async with self.db_pool.acquire() as conn:
                # Basic connectivity test
                result = await conn.fetchval("SELECT 1")
                
                end_time = datetime.utcnow()
                response_time = (end_time - start_time).total_seconds() * 1000
                
                # Get connection count
                conn_count = len(self.db_pool._conns)
                
                # Check for slow queries (simulation)
                slow_queries = await conn.fetchval("""
                    SELECT COUNT(*) FROM pg_stat_activity 
                    WHERE state = 'active' AND query_start < NOW() - INTERVAL '1 minute'
                """)
                
                status = "healthy"
                message = "Database is healthy"
                details = {
                    "active_connections": conn_count,
                    "slow_queries": slow_queries,
                    "pool_utilization": (conn_count / 20) * 100  # Assuming max_pool_size=20
                }
                
                # Determine status based on metrics
                if conn_count > self.alert_thresholds['db_connections_critical']:
                    status = "unhealthy"
                    message = "Too many database connections"
                elif conn_count > self.alert_thresholds['db_connections_warning']:
                    status = "degraded"
                    message = "High database connection count"
                elif slow_queries > 5:
                    status = "degraded"
                    message = "Slow queries detected"
                
                return HealthCheck(
                    service_name="database",
                    status=status,
                    message=message,
                    timestamp=end_time,
                    response_time_ms=response_time,
                    details=details
                )
                
        except Exception as e:
            return HealthCheck(
                service_name="database",
                status="unhealthy",
                message=f"Database health check failed: {str(e)}",
                timestamp=datetime.utcnow(),
                response_time_ms=None,
                details={"error": str(e)}
            )
    
    async def check_service_dependencies(self) -> Dict[str, HealthCheck]:
        """Check health of dependent services."""
        dependencies = {
            "axlerate_gateway": "http://axlerate:8000/health",
            "superset_api": "http://superset:8001/health",
            "auth_service": "http://localhost:8003/health"
        }
        
        health_results = {}
        
        for service_name, health_url in dependencies.items():
            try:
                start_time = datetime.utcnow()
                
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                    async with session.get(health_url) as response:
                        end_time = datetime.utcnow()
                        response_time = (end_time - start_time).total_seconds() * 1000
                        
                        if response.status == 200:
                            health_data = await response.json()
                            status = health_data.get("status", "unknown")
                            message = health_data.get("message", f"Service {service_name} is responding")
                        else:
                            status = "unhealthy"
                            message = f"Service {service_name} returned HTTP {response.status}"
                        
                        health_results[service_name] = HealthCheck(
                            service_name=service_name,
                            status=status,
                            message=message,
                            timestamp=end_time,
                            response_time_ms=response_time,
                            details={"http_status": response.status}
                        )
                        
            except asyncio.TimeoutError:
                health_results[service_name] = HealthCheck(
                    service_name=service_name,
                    status="unhealthy",
                    message=f"Service {service_name} health check timeout",
                    timestamp=datetime.utcnow(),
                    response_time_ms=10000  # 10 second timeout
                )
            except Exception as e:
                health_results[service_name] = HealthCheck(
                    service_name=service_name,
                    status="unhealthy",
                    message=f"Service {service_name} health check failed: {str(e)}",
                    timestamp=datetime.utcnow(),
                    response_time_ms=None,
                    details={"error": str(e)}
                )
        
        return health_results
    
    async def evaluate_system_health(self, metrics: SystemMetrics, 
                                health_checks: Dict[str, HealthCheck]) -> Dict[str, Any]:
        """Evaluate overall system health based on metrics."""
        overall_status = "healthy"
        issues = []
        
        # Evaluate CPU
        if metrics.cpu_percent > self.alert_thresholds['cpu_critical']:
            overall_status = "unhealthy"
            issues.append(f"CPU usage critical: {metrics.cpu_percent}%")
        elif metrics.cpu_percent > self.alert_thresholds['cpu_warning']:
            overall_status = "degraded"
            issues.append(f"CPU usage high: {metrics.cpu_percent}%")
        
        # Evaluate Memory
        if metrics.memory_percent > self.alert_thresholds['memory_critical']:
            overall_status = "unhealthy"
            issues.append(f"Memory usage critical: {metrics.memory_percent}%")
        elif metrics.memory_percent > self.alert_thresholds['memory_warning']:
            overall_status = "degraded"
            issues.append(f"Memory usage high: {metrics.memory_percent}%")
        
        # Evaluate Disk
        if metrics.disk_usage_percent > self.alert_thresholds['disk_critical']:
            overall_status = "unhealthy"
            issues.append(f"Disk usage critical: {metrics.disk_usage_percent}%")
        elif metrics.disk_usage_percent > self.alert_thresholds['disk_warning']:
            overall_status = "degraded"
            issues.append(f"Disk usage high: {metrics.disk_usage_percent}%")
        
        # Evaluate Database
        db_health = health_checks.get("database")
        if db_health:
            if db_health.status == "unhealthy":
                overall_status = "unhealthy"
                issues.append(f"Database unhealthy: {db_health.message}")
            elif db_health.status == "degraded":
                overall_status = "degraded"
                issues.append(f"Database degraded: {db_health.message}")
        
        # Evaluate Service Dependencies
        for service_name, health_check in health_checks.items():
            if health_check.status == "unhealthy":
                overall_status = "unhealthy"
                issues.append(f"Service {service_name} unhealthy: {health_check.message}")
            elif health_check.status == "degraded":
                overall_status = "degraded"
                issues.append(f"Service {service_name} degraded: {health_check.message}")
        
        return {
            "overall_status": overall_status,
            "timestamp": metrics.timestamp,
            "system_metrics": {
                "cpu_percent": metrics.cpu_percent,
                "memory_percent": metrics.memory_percent,
                "disk_usage_percent": metrics.disk_usage_percent,
                "active_connections": metrics.active_connections,
                "database_connections": metrics.database_connections,
                "database_pool_size": metrics.database_pool_size,
                "sync_operations": metrics.sync_operations
            },
            "health_checks": {
                name: {
                    "status": check.status,
                    "message": check.message,
                    "response_time_ms": check.response_time_ms,
                    "details": check.details
                }
                for name, check in health_checks.items()
            },
            "issues": issues,
            "alert_thresholds": self.alert_thresholds
        }
    
    async def log_structured_event(self, event_type: str, level: str, 
                               message: str, details: Dict[str, Any] = None):
        """Log structured event with JSON format."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": "census-monitoring",
            "event_type": event_type,
            "level": level,
            "message": message,
            "details": details or {}
        }
        
        # Output as JSON for log aggregation
        json_log = json.dumps(log_entry, default=str)
        
        if level == "error":
            logger.error(json_log)
        elif level == "warning":
            logger.warning(json_log)
        elif level == "info":
            logger.info(json_log)
        else:
            logger.debug(json_log)
    
    async def start_monitoring_loop(self):
        """Start continuous monitoring loop."""
        logger.info("Starting CENSUS monitoring loop")
        
        while True:
            try:
                # Collect metrics
                metrics = await self.collect_system_metrics()
                
                # Run health checks
                db_health = await self.check_database_health()
                service_health = await self.check_service_dependencies()
                
                health_checks = {"database": db_health}
                health_checks.update(service_health)
                
                # Evaluate overall health
                health_status = await self.evaluate_system_health(metrics, health_checks)
                
                # Log metrics
                await self.log_structured_event(
                    "metrics_collection",
                    "info",
                    "System metrics collected",
                    {"metrics": health_status["system_metrics"]}
                )
                
                # Log health status
                if health_status["overall_status"] != "healthy":
                    await self.log_structured_event(
                        "health_alert",
                        "warning",
                        f"System health degraded: {health_status['overall_status']}",
                        {"issues": health_status["issues"]}
                    )
                
                # Wait for next iteration
                await asyncio.sleep(60)  # Monitor every minute
                
            except Exception as e:
                await self.log_structured_event(
                    "monitoring_error",
                    "error",
                    f"Monitoring loop error: {str(e)}"
                )
                await asyncio.sleep(60)  # Continue monitoring even after error
    
    async def get_monitoring_dashboard(self) -> Dict[str, Any]:
        """Get monitoring dashboard data."""
        try:
            metrics = await self.collect_system_metrics()
            db_health = await self.check_database_health()
            service_health = await self.check_service_dependencies()
            
            health_checks = {"database": db_health}
            health_checks.update(service_health)
            
            return await self.evaluate_system_health(metrics, health_checks)
            
        except Exception as e:
            return {
                "error": f"Failed to get monitoring data: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def close(self):
        """Close monitoring system."""
        if self.db_pool:
            await self.db_pool.close()
            logger.info("CENSUS monitoring shutdown")

# Global monitoring instance
census_monitoring = None

async def get_census_monitoring() -> CENUSMonitoring:
    """Get or create monitoring instance."""
    global census_monitoring
    if census_monitoring is None:
        db_url = os.getenv("CENSUS_DB_URL", "postgresql://census_user:census_password@localhost:5432/census_db")
        census_monitoring = CENUSMonitoring(db_url)
        await census_monitoring.initialize()
    return census_monitoring

if __name__ == "__main__":
    async def main():
        """Test the monitoring system."""
        monitoring = await get_census_monitoring()
        
        try:
            # Get current metrics
            dashboard = await monitoring.get_monitoring_dashboard()
            
            # Print dashboard
            print("=== CENSUS Monitoring Dashboard ===")
            print(f"Overall Status: {dashboard['overall_status']}")
            print(f"Timestamp: {dashboard['timestamp']}")
            print("\nSystem Metrics:")
            for key, value in dashboard['system_metrics'].items():
                print(f"  {key}: {value}")
            
            print("\nHealth Checks:")
            for name, check in dashboard['health_checks'].items():
                print(f"  {name}: {check.status} ({check.message})")
            
            if dashboard['issues']:
                print("\nIssues:")
                for issue in dashboard['issues']:
                    print(f"  - {issue}")
            
            # Start monitoring loop
            await monitoring.start_monitoring_loop()
            
        finally:
            await monitoring.close()
    
    asyncio.run(main())
