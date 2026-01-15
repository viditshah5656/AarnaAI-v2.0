'use client';

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faChartLine, faNewspaper, faBrain, faGears, faRightFromBracket } from '@fortawesome/free-solid-svg-icons';

const Sidebar = () => {
  const navItems = [
    { icon: faChartLine, text: 'Dashboard' },
    { icon: faNewspaper, text: 'News' },
    { icon: faBrain, text: 'AI Analysis' },
    { icon: faGears, text: 'Settings' },
  ];

  return (
    <div className="w-64 bg-sidebar p-6 flex flex-col justify-between">
      <div>
        <div className="flex items-center mb-12">
          <h1 className="text-2xl font-bold text-text-primary">Aarna AI</h1>
        </div>
        <nav>
          <ul>
            {navItems.map((item, index) => (
              <li key={index} className="mb-4">
                <a href="#" className="flex items-center p-2 rounded-lg text-text-secondary hover:bg-accent hover:text-white transition-colors">
                  <FontAwesomeIcon icon={item.icon} className="w-5 h-5 mr-3" />
                  <span>{item.text}</span>
                </a>
              </li>
            ))}
          </ul>
        </nav>
      </div>
      <div>
        <a href="#" className="flex items-center p-2 rounded-lg text-text-secondary hover:bg-accent hover:text-white transition-colors">
          <FontAwesomeIcon icon={faRightFromBracket} className="w-5 h-5 mr-3" />
          <span>Logout</span>
        </a>
      </div>
    </div>
  );
};

export default Sidebar;
