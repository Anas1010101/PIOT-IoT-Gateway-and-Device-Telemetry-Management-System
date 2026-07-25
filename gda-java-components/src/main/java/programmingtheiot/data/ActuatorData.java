package programmingtheiot.data;

import java.io.Serializable;

import programmingtheiot.common.ConfigConst;

public class ActuatorData extends BaseIotData implements Serializable
{
	private static final long serialVersionUID = 1L;

	private int     command    = ConfigConst.DEFAULT_COMMAND;
	private float   value      = ConfigConst.DEFAULT_VAL;
	private boolean isResponse = false;
	private String  stateData  = "";

	public ActuatorData()
	{
		super();
	}

	public int getCommand()
	{
		return this.command;
	}

	public String getStateData()
	{
		return this.stateData;
	}

	public float getValue()
	{
		return this.value;
	}

	public boolean isResponseFlagEnabled()
	{
		return this.isResponse;
	}

	public void setAsResponse()
	{
		updateTimeStamp();
		this.isResponse = true;
	}

	public void setCommand(int command)
	{
		updateTimeStamp();
		this.command = command;
	}

	public void setStateData(String stateData)
	{
		updateTimeStamp();

		if (stateData != null) {
			this.stateData = stateData;
		}
	}

	public void setValue(float val)
	{
		updateTimeStamp();
		this.value = val;
	}

	@Override
	protected void handleUpdateData(BaseIotData data)
	{
		if (data instanceof ActuatorData) {
			ActuatorData aData = (ActuatorData) data;

			this.setCommand(aData.getCommand());
			this.setValue(aData.getValue());
			this.setStateData(aData.getStateData());

			if (aData.isResponseFlagEnabled()) {
				this.setAsResponse();
			}
		}
	}

    public void _handleUpdateData(ActuatorData data) {
        throw new UnsupportedOperationException("Not supported yet.");
    }
}