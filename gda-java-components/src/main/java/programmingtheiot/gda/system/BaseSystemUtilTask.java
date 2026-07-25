package programmingtheiot.gda.system;

import java.util.logging.Logger;

import programmingtheiot.common.ConfigConst;

public abstract class BaseSystemUtilTask
{
	// static
	private static final Logger _Logger =
		Logger.getLogger(BaseSystemUtilTask.class.getName());

	// private
	private String name = ConfigConst.NOT_SET;
	private int typeID = ConfigConst.DEFAULT_TYPE_ID;

	// constructors
	public BaseSystemUtilTask(String name, int typeID)
	{
		super();

		if (name != null) {
			this.name = name;
		}

		this.typeID = typeID;
	}

	// public methods
	public String getName()
	{
		return this.name;
	}

	public int getTypeID()
	{
		return this.typeID;
	}

	// abstract method
	public abstract float getTelemetryValue();
}