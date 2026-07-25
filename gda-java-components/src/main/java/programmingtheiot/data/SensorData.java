package programmingtheiot.data;

import java.io.Serializable;

import programmingtheiot.common.ConfigConst;

public class SensorData extends BaseIotData implements Serializable
{
	private static final long serialVersionUID = 1L;

	private float value = ConfigConst.DEFAULT_VAL;

	public SensorData()
	{
		super();
	}

	public float getValue()
	{
		return this.value;
	}

	public void setValue(float val)
	{
		updateTimeStamp();
		this.value = val;
	}

	@Override
	protected void handleUpdateData(BaseIotData data)
	{
		if (data instanceof SensorData) {
			SensorData sData = (SensorData) data;
			this.setValue(sData.getValue());
		}
	}
}