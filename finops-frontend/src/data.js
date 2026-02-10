import axios from "axios";

export const fetchSavingsData = async () => {
  try {
    const res = await axios.get("http://localhost:5000/api/savings");
    return res.data.data || [];
  } catch (error) {
    console.error("❌ Failed to fetch savings data", error);
    return [];
  }
};

export const fetchCostingData = async () => {
  try {
    const res = await axios.get("http://localhost:5000/api/costing/current");
    return res.data;
  } catch (error) {
    console.error("❌ Failed to fetch costing data", error);
    return null;
  }
};

export const fetchCostingByRegion = async () => {
  try {
    const res = await axios.get("http://localhost:5000/api/costing/by-region");
    return res.data;
  } catch (error) {
    console.error("❌ Failed to fetch regional costing data", error);
    return [];
  }
};

export const fetchCostingByService = async () => {
  try {
    const res = await axios.get("http://localhost:5000/api/costing/by-service");
    return res.data;
  } catch (error) {
    console.error("❌ Failed to fetch service costing data", error);
    return null;
  }
};

export const fetchResizeOptions = async (instanceId) => {
  try {
    const res = await axios.get(`http://localhost:5000/api/instances/${instanceId}/resize-options`);
    return res.data;
  } catch (error) {
    console.error(`❌ Failed to fetch resize options for ${instanceId}`, error);
    return [];
  }
};
