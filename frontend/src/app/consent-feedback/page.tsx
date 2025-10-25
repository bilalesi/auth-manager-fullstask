"use client";

import { SharedLayout } from "@/layout/default";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";

function ConsentContent() {
  const searchParams = useSearchParams();
  const error = searchParams.get("error");
  const description = searchParams.get("description");

  const isSuccess = !error && !description;

  const getIcon = () => {
    if (isSuccess) {
      return (
        <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-green-100 dark:bg-green-900/20">
          <svg
            className="h-10 w-10 text-green-600 dark:text-green-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 13l4 4L19 7"
            />
          </svg>
        </div>
      );
    }

    return (
      <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/20">
        <svg
          className="h-10 w-10 text-red-600 dark:text-red-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </div>
    );
  };

  const getTitle = () => {
    if (isSuccess) {
      return "Consent Granted Successfully";
    }
    return "Consent Error";
  };

  const getMessage = () => {
    if (isSuccess) {
      return "Your consent has been recorded and accepted.";
    }
    return "An error occurred during the consent process";
  };

  const getDescription = () => {
    if (isSuccess) {
      return "You can now close this window and return to your application.";
    }
    return "Please try again or contact support if this error persists.";
  };

  const getButtonColor = () => {
    if (isSuccess) {
      return "bg-teal-500 hover:bg-teal-600 focus:ring-teal-600";
    }
    return "bg-red-500 hover:bg-red-600 focus:ring-red-600";
  };

  return (
    <SharedLayout>
      <div className="flex flex-col items-center justify-center space-y-8 p-8">
        <div className="text-center">
          {getIcon()}

          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
            {getTitle()}
          </h1>

          <p className="text-lg text-gray-600 dark:text-gray-300 mb-2">
            {getMessage()}
          </p>

          <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
            {getDescription()}
          </p>

          {/* Debug info for development */}
          {process.env.NODE_ENV === "development" && (error || description) && (
            <div className="mt-6 p-4 bg-gray-100 dark:bg-gray-800 rounded-lg text-left">
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
                Debug Information:
              </p>
              {error && <p className="text-xs">Error Code: {error}</p>}
              {description && (
                <p className="text-xs">Description: {description}</p>
              )}
            </div>
          )}
        </div>

        <div className="flex flex-col sm:flex-row gap-4">
          <Link
            href="/"
            className="inline-flex justify-center items-center rounded-md border border-transparent px-8 py-3 text-base font-medium text-white shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors duration-200 bg-teal-500 hover:bg-teal-600 focus:ring-teal-600"
          >
            Back to Application
          </Link>
        </div>
      </div>
    </SharedLayout>
  );
}

export default function ConsentPage() {
  return (
    <Suspense
      fallback={
        <SharedLayout>
          <div className="flex items-center justify-center p-8">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-500 mx-auto mb-4"></div>
              <p className="text-gray-600 dark:text-gray-400">Loading...</p>
            </div>
          </div>
        </SharedLayout>
      }
    >
      <ConsentContent />
    </Suspense>
  );
}
