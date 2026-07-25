package programmingtheiot.data;

import java.io.Serializable;

import programmingtheiot.common.ConfigConst;

public class SystemPerformanceData extends BaseIotData implements Serializable
{
	private static final long serialVersionUID = 1L;

	private float cpuUtil  = ConfigConst.DEFAULT_VAL;
	private float diskUtil = ConfigConst.DEFAULT_VAL;
	private float memUtil  = ConfigConst.DEFAULT_VAL;

	public SystemPerformanceData()
{
	super();

	super.setName(ConfigConst.SYS_PERF_DATA);
	super.setTypeID(ConfigConst.SYSTEM_PERF_TYPE);
}
	public float getCpuUtilization()
	{
		return this.cpuUtil;
	}

	public float getDiskUtilization()
	{
		return this.diskUtil;
	}

	public float getMemoryUtilization()
	{
		return this.memUtil;
	}

	public void setCpuUtilization(float cpuUtil)
	{
		updateTimeStamp();
		this.cpuUtil = cpuUtil;
	}

	public void setDiskUtilization(float diskUtil)
	{
		updateTimeStamp();
		this.diskUtil = diskUtil;
	}

	public void setMemoryUtilization(float memUtil)
	{
		updateTimeStamp();
		this.memUtil = memUtil;
	}

	@Override
	protected void handleUpdateData(BaseIotData data)
	{
		if (data instanceof SystemPerformanceData) {
			SystemPerformanceData spData = (SystemPerformanceData) data;

			this.setCpuUtilization(spData.getCpuUtilization());
			this.setDiskUtilization(spData.getDiskUtilization());
			this.setMemoryUtilization(spData.getMemoryUtilization());
		}
	}
}