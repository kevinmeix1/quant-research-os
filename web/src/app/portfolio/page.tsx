import { Suspense } from "react";
import PortfolioPage from "./PortfolioClient";

export default function Page() {
  return (
    <Suspense
      fallback={
        <div className="page">
          <div className="skeleton" style={{ width: 200 }} />
        </div>
      }
    >
      <PortfolioPage />
    </Suspense>
  );
}
