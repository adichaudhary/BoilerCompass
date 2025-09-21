import React from 'react';

interface StarterButtonProps {
    onSelect: (prompt: string) => void;
}

export const StarterButtons: React.FC<StarterButtonProps> = ({ onSelect }) => {
    const suggestions = [
        {
            icon: "📅",
            title: "Find Events This Week",
            description: "Browse upcoming events at Purdue",
            prompt: "What events are happening at Purdue this week?"
        },
        {
            icon: "🏈",
            title: "Sports Schedule",
            description: "Check Purdue sports games and schedules",
            prompt: "What are the upcoming Purdue sports events?"
        },
        {
            icon: "🍝",
            title: "Dining Options",
            description: "Find concerts and shows",
            prompt: "Find dining locations that follow these dietary restrictions: "
        },
        {
            icon: "📖",
            title: "Study Locations",
            description: "Discover open study spots",
            prompt: "Find optimal study locations on campus"
        }
    ]; return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl mx-auto px-6 py-8">
            {suggestions.map((suggestion, index) => (
                <button
                    key={index}
                    onClick={() => onSelect(suggestion.prompt)}
                    className="flex items-start space-x-4 p-6 rounded-2xl bg-white/5 hover:bg-white/10 border border-white/10 transition-all duration-200 hover:shadow-lg text-left group"
                >
                    <div className="p-3 rounded-xl bg-yellow-500/10 text-yellow-500 group-hover:bg-yellow-500 group-hover:text-black transition-all duration-200">
                        {suggestion.icon}
                    </div>
                    <div>
                        <h3 className="text-lg font-medium text-white mb-1">{suggestion.title}</h3>
                        <p className="text-sm text-gray-400">{suggestion.description}</p>
                    </div>
                </button>
            ))}
        </div>
    );
};