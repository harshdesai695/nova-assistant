"""
System Information Skill for N.O.V.A
Provides detailed information about system resources and hardware.
"""

import psutil
import platform
from datetime import datetime
from core.registry import skill


@skill
def get_system_info():
    """Get complete system information."""
    try:
        # OS Information
        os_name = platform.system()
        os_version = platform.release()
        
        # CPU Information
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count(logical=True)
        cpu_freq = psutil.cpu_freq()
        
        # Memory Information
        memory = psutil.virtual_memory()
        memory_total_gb = memory.total / (1024 ** 3)
        memory_used_gb = memory.used / (1024 ** 3)
        memory_percent = memory.percent
        
        # Disk Information
        disk = psutil.disk_usage('/')
        disk_total_gb = disk.total / (1024 ** 3)
        disk_used_gb = disk.used / (1024 ** 3)
        disk_percent = disk.percent
        
        # Battery (if available)
        battery_info = ""
        if hasattr(psutil, "sensors_battery"):
            battery = psutil.sensors_battery()
            if battery:
                battery_percent = battery.percent
                plugged = "plugged in" if battery.power_plugged else "on battery"
                battery_info = f" Battery is at {battery_percent}% and {plugged}."
        
        response = (
            f"System Status: Running {os_name} {os_version}. "
            f"CPU usage is at {cpu_percent}% across {cpu_count} cores. "
            f"Memory: {memory_used_gb:.1f} GB used out of {memory_total_gb:.1f} GB ({memory_percent}%). "
            f"Disk: {disk_used_gb:.1f} GB used out of {disk_total_gb:.1f} GB ({disk_percent}%)."
            f"{battery_info}"
        )
        
        return response
        
    except Exception as e:
        return f"Unable to retrieve system information: {str(e)}"


@skill
def get_cpu_usage():
    """Get CPU usage."""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count(logical=True)
        
        if cpu_percent < 30:
            status = "running smoothly"
        elif cpu_percent < 70:
            status = "moderately busy"
        else:
            status = "under heavy load"
        
        return f"CPU is {status} at {cpu_percent}% usage across {cpu_count} cores."
        
    except Exception as e:
        return f"Unable to get CPU usage: {str(e)}"


@skill
def get_memory_usage():
    """Get memory usage."""
    try:
        memory = psutil.virtual_memory()
        total_gb = memory.total / (1024 ** 3)
        used_gb = memory.used / (1024 ** 3)
        available_gb = memory.available / (1024 ** 3)
        percent = memory.percent
        
        if percent < 50:
            status = "plenty of memory available"
        elif percent < 80:
            status = "memory usage is moderate"
        else:
            status = "memory is running low"
        
        return (
            f"Memory usage: {used_gb:.1f} GB used out of {total_gb:.1f} GB total. "
            f"You have {available_gb:.1f} GB available ({100-percent:.1f}% free). "
            f"Status: {status}."
        )
        
    except Exception as e:
        return f"Unable to get memory usage: {str(e)}"


@skill
def get_disk_usage():
    """Get disk usage."""
    try:
        disk = psutil.disk_usage('/')
        total_gb = disk.total / (1024 ** 3)
        used_gb = disk.used / (1024 ** 3)
        free_gb = disk.free / (1024 ** 3)
        percent = disk.percent
        
        if percent < 70:
            status = "plenty of space"
        elif percent < 90:
            status = "getting full"
        else:
            status = "critically low on space"
        
        return (
            f"Disk usage: {used_gb:.1f} GB used out of {total_gb:.1f} GB total. "
            f"You have {free_gb:.1f} GB free ({100-percent:.1f}% available). "
            f"Status: {status}."
        )
        
    except Exception as e:
        return f"Unable to get disk usage: {str(e)}"


@skill
def get_battery_status():
    """Get battery information."""
    try:
        if not hasattr(psutil, "sensors_battery"):
            return "Battery information is not available on this system."
        
        battery = psutil.sensors_battery()
        
        if battery is None:
            return "No battery detected. This might be a desktop computer."
        
        percent = battery.percent
        plugged = battery.power_plugged
        
        if plugged:
            status = "charging" if percent < 100 else "fully charged"
            return f"Battery is at {percent}% and {status}."
        else:
            # Estimate time remaining
            if battery.secsleft != psutil.POWER_TIME_UNLIMITED:
                hours = battery.secsleft // 3600
                minutes = (battery.secsleft % 3600) // 60
                time_left = f"{hours}h {minutes}m"
                return f"Battery is at {percent}% with approximately {time_left} remaining."
            else:
                return f"Battery is at {percent}% and discharging."
        
    except Exception as e:
        return f"Unable to get battery status: {str(e)}"


@skill
def get_network_stats():
    """Get network statistics."""
    try:
        net_io = psutil.net_io_counters()
        bytes_sent_mb = net_io.bytes_sent / (1024 ** 2)
        bytes_recv_mb = net_io.bytes_recv / (1024 ** 2)
        
        return (
            f"Network statistics: "
            f"{bytes_sent_mb:.1f} MB sent, "
            f"{bytes_recv_mb:.1f} MB received since last boot."
        )
        
    except Exception as e:
        return f"Unable to get network statistics: {str(e)}"


@skill
def get_system_uptime():
    """Get system uptime."""
    try:
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        current_time = datetime.now()
        uptime_delta = current_time - boot_time
        
        days = uptime_delta.days
        hours = uptime_delta.seconds // 3600
        minutes = (uptime_delta.seconds % 3600) // 60
        
        if days > 0:
            uptime_str = f"{days} days, {hours} hours, and {minutes} minutes"
        elif hours > 0:
            uptime_str = f"{hours} hours and {minutes} minutes"
        else:
            uptime_str = f"{minutes} minutes"
        
        boot_time_str = boot_time.strftime("%B %d at %I:%M %p")
        
        return (
            f"System has been running for {uptime_str}. "
            f"Last boot was on {boot_time_str}."
        )
        
    except Exception as e:
        return f"Unable to get system uptime: {str(e)}"


@skill
def get_running_processes():
    """Get information about running processes."""
    try:
        # Get process count
        process_count = len(psutil.pids())
        
        # Get top 3 processes by CPU
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Sort by CPU usage
        top_processes = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:3]
        
        top_list = ", ".join([f"{p['name']} ({p['cpu_percent']}%)" for p in top_processes if p['cpu_percent'] > 0])
        
        if top_list:
            return (
                f"There are {process_count} processes running. "
                f"Top CPU users: {top_list}."
            )
        else:
            return f"There are {process_count} processes running."
        
    except Exception as e:
        return f"Unable to get process information: {str(e)}"


@skill
def get_temperature():
    """Get system temperature."""
    try:
        if not hasattr(psutil, "sensors_temperatures"):
            return "Temperature sensors are not available on this system."
        
        temps = psutil.sensors_temperatures()
        
        if not temps:
            return "No temperature sensors detected on this system."
        
        # Try to get CPU temperature
        cpu_temp = None
        for name, entries in temps.items():
            if 'coretemp' in name.lower() or 'cpu' in name.lower():
                for entry in entries:
                    if entry.current:
                        cpu_temp = entry.current
                        break
                if cpu_temp:
                    break
        
        if cpu_temp:
            if cpu_temp < 60:
                status = "running cool"
            elif cpu_temp < 80:
                status = "at normal temperature"
            else:
                status = "running hot"
            
            return f"CPU temperature is {cpu_temp}°C, {status}."
        else:
            return "CPU temperature information is not available."
        
    except Exception as e:
        return f"Unable to get temperature: {str(e)}"