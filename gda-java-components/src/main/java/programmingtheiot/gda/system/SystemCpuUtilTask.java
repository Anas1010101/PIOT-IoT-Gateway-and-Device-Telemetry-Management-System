package programmingtheiot.gda.system;

import java.lang.management.ManagementFactory;
import java.lang.management.OperatingSystemMXBean;

import programmingtheiot.common.ConfigConst;

public class SystemCpuUtilTask extends BaseSystemUtilTask
{
	// constructors
	
	public SystemCpuUtilTask()
	{
		super(ConfigConst.NOT_SET, ConfigConst.DEFAULT_TYPE_ID);
	}
	
	
	// public methods
	
	@Override
	public float getTelemetryValue()
	{
		OperatingSystemMXBean mxBean =
			ManagementFactory.getOperatingSystemMXBean();

		double cpuUtil = mxBean.getSystemLoadAverage();

		return (float) cpuUtil;
	}
}