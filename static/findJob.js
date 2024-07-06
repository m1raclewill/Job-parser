document.getElementById('search_button').addEventListener('click', function() {
    const jobTitle = document.getElementById('job_title').value;
    const city = document.getElementById('city').value;
    const company = document.getElementById('company').value;

    fetch(`/search?job_title=${jobTitle}&city=${city}&company=${company}`)
        .then(response => response.json())
        .then(data => {
            const jobList = document.getElementById('job_list');
            jobList.innerHTML = '';
            data.jobs.forEach(job => {
                const jobItem = document.createElement('div');
                jobItem.classList.add('job-item');
                jobItem.innerHTML = `
                    <h2>${job.title}</h2>
                    <p>Company: ${job.company}</p>
                    <p>Salary: ${job.salary}</p>
                    <p>Experience: ${job.experience}</p>
                    <p>City: ${job.city}</p>
                `;
                jobList.appendChild(jobItem);
            });
        });
});

