import { useState } from "react";
import Dashboard from "./Dashboard";
import ResourceDetail from "./ResourceDetail";

function App() {
  const [currentPage, setCurrentPage] = useState("dashboard");
  const [selectedResource, setSelectedResource] = useState(null);

  const handleViewDetails = (resourceId, resourceType) => {
    setSelectedResource({ id: resourceId, type: resourceType });
    setCurrentPage("detail");
  };

  const handleBackToDashboard = () => {
    setCurrentPage("dashboard");
    setSelectedResource(null);
  };

  return (
    <>
      {currentPage === "dashboard" ? (
        <Dashboard onViewDetails={handleViewDetails} />
      ) : (
        <ResourceDetail 
          resource={selectedResource} 
          onBack={handleBackToDashboard} 
        />
      )}
    </>
  );
}

export default App;
