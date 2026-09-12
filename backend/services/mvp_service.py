from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import joblib
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder

from backend.services.data_service import data_service
from backend.services.risk_service import risk_engine

INTERVENTIONS = [
    {"id": "speed_enforcement", "name": "Speed enforcement camera", "factors": ["overspeeding", "traffic"], "effectiveness": 0.28, "cost": "High", "difficulty": "Medium", "timeframe": "3-6 months", "confidence": "Prototype estimate"},
    {"id": "traffic_calming", "name": "Speed calming and rumble strips", "factors": ["overspeeding", "junction risk"], "effectiveness": 0.22, "cost": "Medium", "difficulty": "Medium", "timeframe": "1-3 months", "confidence": "Prototype estimate"},
    {"id": "street_lighting", "name": "Improve street lighting", "factors": ["poor lighting", "night risk", "visibility"], "effectiveness": 0.25, "cost": "Medium", "difficulty": "Medium", "timeframe": "1-3 months", "confidence": "Prototype scenario estimate"},
    {"id": "pedestrian_crossing", "name": "Protected pedestrian crossing", "factors": ["pedestrian risk", "vulnerable users"], "effectiveness": 0.24, "cost": "Medium", "difficulty": "Medium", "timeframe": "1-3 months", "confidence": "Prototype estimate"},
    {"id": "road_repair", "name": "Resurface and improve lane markings", "factors": ["poor road condition", "potholes"], "effectiveness": 0.20, "cost": "High", "difficulty": "High", "timeframe": "3-6 months", "confidence": "Prototype estimate"},
    {"id": "junction_audit", "name": "Junction signal and channelisation audit", "factors": ["junction risk", "wrong-side driving"], "effectiveness": 0.18, "cost": "Medium", "difficulty": "Medium", "timeframe": "1-3 months", "confidence": "Prototype estimate"},
]


class MVPService:
    def __init__(self) -> None:
        self.model = None
        self.metrics: Dict[str, Any] = {"status": "not trained", "prototype": True}

    def locations(self, filters: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        frame = data_service.get_df().copy()
        for key, value in (filters or {}).items():
            if value and key in frame.columns:
                frame = frame[frame[key].astype(str) == value]
        results = []
        for location_id, group in frame.groupby("location_id"):
            risk = risk_engine.calculate_corridor_risk(location_id, group)
            first = group.iloc[0]
            results.append({"id": location_id, "road_name": first.road_name, "road_segment": first.road_segment, "state": first.state, "district": first.district, "city": first.city, "road_category": first.road_category, "latitude": round(float(group.latitude.mean()), 6), "longitude": round(float(group.longitude.mean()), 6), "accidents": int(group.accidents.sum()), "fatalities": int(group.fatalities.sum()), "injuries": int(group.injuries.sum()), "risk_score": risk["risk_score"], "risk_level": risk["risk_level"]})
        return sorted(results, key=lambda item: item["risk_score"], reverse=True)

    def location(self, location_id: str) -> Dict[str, Any]:
        match = next((item for item in self.locations() if item["id"] == location_id), None)
        if not match:
            raise KeyError(location_id)
        group = data_service.get_df().query("location_id == @location_id")
        causes = group.groupby("cause").agg(accidents=("accidents", "sum"), fatalities=("fatalities", "sum")).reset_index().sort_values("accidents", ascending=False)
        users = group.groupby("vehicle_type")["accidents"].sum().sort_values(ascending=False)
        hours = group.groupby("hour")["accidents"].sum().sort_values(ascending=False)
        risk = risk_engine.calculate_corridor_risk(location_id, group)
        top_cause = str(causes.iloc[0].cause) if len(causes) else "Unknown"
        top_user = str(users.index[0]) if len(users) else "Unknown"
        peak_hour = int(hours.index[0]) if len(hours) else 0
        lighting = str(group["lighting_condition"].mode().iloc[0]) if not group["lighting_condition"].mode().empty else "Unknown"
        road_condition = str(group["road_condition"].mode().iloc[0]) if not group["road_condition"].mode().empty else "Unknown"
        traffic = str(group["traffic_level"].mode().iloc[0]) if not group["traffic_level"].mode().empty else "Unknown"
        return {**match, "risk": risk, "top_cause": top_cause, "top_user": top_user, "peak_hour": peak_hour, "lighting_condition": lighting, "road_condition": road_condition, "traffic_level": traffic, "causes": [{"cause": str(row["cause"]), "accidents": int(row["accidents"]), "fatalities": int(row["fatalities"])} for row in causes.to_dict("records")], "vulnerability": [{"user": str(index), "accidents": int(value)} for index, value in users.items()], "temporal": [{"hour": int(index), "accidents": int(value)} for index, value in group.groupby("hour")["accidents"].sum().sort_index().items()], "trend": [{"year": int(index), "accidents": int(value)} for index, value in group.groupby("year")["accidents"].sum().sort_index().items()], "explanation": f"Risk is {risk['risk_level'].lower()} primarily due to {top_cause.lower()}, {top_user.lower()} involvement, and concentration around {peak_hour:02d}:00."}

    def interventions(self, location_id: str) -> List[Dict[str, Any]]:
        detail = self.location(location_id)
        text = f"{detail['top_cause']} {detail['top_user']} {detail['lighting_condition']} {detail['road_condition']} {detail['traffic_level']} hour {detail['peak_hour']}".lower()
        aliases = {"poor lighting": ["poor lighting", "unlit", "pitch black", "intermittent"], "night risk": ["hour 21", "hour 22", "hour 23", "hour 0", "hour 1", "hour 2", "hour 3", "hour 4"], "visibility": ["lighting", "unlit"], "potholes": ["pothole", "damaged"], "poor road condition": ["damaged", "wet", "under construction"], "pedestrian exposure": ["pedestrian"], "vulnerable users": ["vulnerable", "two-wheeler", "pedestrian", "auto-rickshaw"], "overspeeding": ["overspeed"], "junction risk": ["junction", "intersection"], "traffic": ["high", "congested"]}
        ranked = []
        for item in INTERVENTIONS:
            matched_factors = [factor for factor in item["factors"] if any(alias in text for alias in aliases.get(factor, [factor]))]
            matches = len(matched_factors)
            ranked.append({**item, "matched_factors": matched_factors, "priority_score": round(item["effectiveness"] * 100 + matches * 18 + detail["risk"]["risk_score"] * 0.25, 1), "reason": f"Matches {', '.join(matched_factors) if matched_factors else 'general road safety'} supported signal(s) in this location."})
        return sorted(ranked, key=lambda item: item["priority_score"], reverse=True)

    def simulate(self, location_id: str, intervention_ids: List[str]) -> Dict[str, Any]:
        base = float(self.location(location_id)["risk"]["risk_score"])
        selected = [item for item in INTERVENTIONS if item["id"] in intervention_ids or (item["id"] == "street_lighting" and "lighting_upgrade" in intervention_ids)]
        ranked = {item["id"]: item for item in self.interventions(location_id)}
        effectiveness = [item["effectiveness"] * (1.0 if ranked.get(item["id"], {}).get("matched_factors") else 0.1) for item in selected]
        reduction = 1 - np.prod([1 - value for value in effectiveness]) if effectiveness else 0
        scenario = round(max(0.0, min(100.0, base * (1 - reduction))), 1)
        return {"location_id": location_id, "current_risk": base, "scenario_risk": scenario, "estimated_reduction": round(base - scenario, 1), "estimated_reduction_percent": round((base - scenario) / base * 100, 1) if base else 0, "interventions": selected, "label": "Scenario-Based Estimated Impact", "disclaimer": "These estimates support planning and comparison. They do not represent guaranteed accident reductions without validated intervention outcome data."}

    def train(self) -> Dict[str, Any]:
        frame = data_service.get_df().copy()
        features = ["year", "month", "hour", "road_category", "cause", "vehicle_type", "weather", "road_condition", "lighting_condition", "traffic_level"]
        frame["severity_target"] = frame.accidents + 3 * frame.injuries + 5 * frame.fatalities
        numeric = ["year", "month", "hour"]
        categorical = [column for column in features if column not in numeric]
        transformer = ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore"), categorical)], remainder="passthrough")
        x, y = transformer.fit_transform(frame[features]), frame["severity_target"]
        x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.25, random_state=42) if len(frame) >= 8 else (x, x, y, y)
        model = RandomForestRegressor(n_estimators=120, random_state=42)
        model.fit(x_train, y_train)
        predictions = model.predict(x_test)
        self.model = (transformer, model, features)
        joblib.dump(self.model, "backend/ml/road_risk_rf.joblib")
        self.metrics = {"task": "severity proxy regression", "prototype": True, "records": len(frame), "mae": round(float(mean_absolute_error(y_test, predictions)), 3), "rmse": round(float(mean_squared_error(y_test, predictions) ** 0.5), 3), "r2": round(float(r2_score(y_test, predictions)), 3) if len(y_test) > 1 else None}
        return self.metrics

    def prediction(self, location_id: str) -> Dict[str, Any]:
        detail = self.location(location_id)
        if self.model is None:
            self.train()
        group = data_service.get_df().query("location_id == @location_id").copy()
        transformer, model, features = self.model
        predicted_raw = float(model.predict(transformer.transform(group[features])).mean())
        observed = data_service.get_df().assign(severity_target=lambda frame: frame.accidents + 3 * frame.injuries + 5 * frame.fatalities).groupby("location_id")["severity_target"].mean()
        predicted_component = min(35.0, max(0.0, predicted_raw / max(float(observed.max()), 1.0) * 35.0))
        components = detail["risk"]["component_scores"]
        predicted_score = round(float(np.clip(predicted_component + sum(value for key, value in components.items() if key != "severity_frequency"), 0, 100)), 1)
        years = detail["trend"]
        trend = "Increasing" if len(years) > 1 and years[-1]["accidents"] > years[-2]["accidents"] else "Decreasing" if len(years) > 1 and years[-1]["accidents"] < years[-2]["accidents"] else "Stable"
        importance = sorted(zip(transformer.get_feature_names_out(), model.feature_importances_), key=lambda pair: pair[1], reverse=True)[:5]
        return {"location_id": location_id, "current_risk": detail["risk"]["risk_score"], "predicted_risk": predicted_score, "predicted_level": risk_engine.classify_risk_level(predicted_score), "trend": trend, "model_type": "RandomForestRegressor severity proxy", "important_features": [{"feature": name, "importance": round(float(value), 4)} for name, value in importance], "metrics": self.metrics, "limitation": "Prototype estimate; normalized risk score is not an accident probability."}

    def summary(self) -> Dict[str, Any]:
        frame, locations = data_service.get_df(), self.locations()
        users = frame.groupby("vehicle_type")["accidents"].sum().sort_values(ascending=False)
        hours = frame.groupby("hour")["accidents"].sum().sort_values(ascending=False)
        yearly = frame.groupby("year").agg(accidents=("accidents", "sum"), fatalities=("fatalities", "sum"), injuries=("injuries", "sum")).sort_index()
        causes = frame.groupby("cause")["accidents"].sum().sort_values(ascending=False)
        return {"is_demo": data_service.is_demo(), "data_label": "DEMO / SYNTHETIC DATA" if data_service.is_demo() else "USER DATA", "total_accidents": int(frame.accidents.sum()), "total_fatalities": int(frame.fatalities.sum()), "total_injuries": int(frame.injuries.sum()), "critical_risk_roads": sum(item["risk_level"] == "Critical" for item in locations), "high_risk_roads": sum(item["risk_level"] == "High" for item in locations), "average_risk_score": round(float(np.mean([item["risk_score"] for item in locations])), 1) if locations else 0, "highest_risk_location": locations[0] if locations else None, "most_vulnerable_user": str(users.index[0]) if len(users) else "Unknown", "peak_risk_hour": int(hours.index[0]) if len(hours) else 0, "risk_distribution": pd.Series([item["risk_level"] for item in locations]).value_counts().to_dict(), "trend": [{"year": int(index), "accidents": int(row.accidents), "fatalities": int(row.fatalities), "injuries": int(row.injuries)} for index, row in yearly.iterrows()], "top_causes": [{"name": str(index), "value": int(value)} for index, value in causes.head(6).items()], "vulnerable_users": [{"name": str(index), "value": int(value)} for index, value in users.head(6).items()]}

mvp_service = MVPService()